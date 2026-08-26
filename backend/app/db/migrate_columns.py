"""Ensure new voucher settlement columns exist (SQLite-friendly)."""

import re

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_voucher_settlement_columns(engine: Engine) -> None:
    insp = inspect(engine)
    if "vouchers" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("vouchers")}
    alters: list[str] = []
    if "settlement_type" not in existing:
        alters.append("ALTER TABLE vouchers ADD COLUMN settlement_type VARCHAR(32)")
    if "bank_name" not in existing:
        alters.append("ALTER TABLE vouchers ADD COLUMN bank_name VARCHAR(120)")
    if "settlement_date" not in existing:
        alters.append("ALTER TABLE vouchers ADD COLUMN settlement_date DATE")
    if "file_number" not in existing:
        alters.append("ALTER TABLE vouchers ADD COLUMN file_number VARCHAR(100)")
    if not alters:
        return
    with engine.begin() as conn:
        for stmt in alters:
            conn.execute(text(stmt))


def flatten_vouchers_drop_line_items(engine: Engine) -> None:
    """Merge voucher_line_items into vouchers (classification/details),
    drop remarks/notes/source_file_url and voucher_line_items."""
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    if "vouchers" not in tables:
        return

    dialect = engine.dialect.name
    cols = {c["name"] for c in insp.get_columns("vouchers")}

    with engine.begin() as conn:
        if "classification" not in cols:
            if dialect == "postgresql":
                conn.execute(
                    text("ALTER TABLE vouchers ADD COLUMN classification VARCHAR(100) NOT NULL DEFAULT ''")
                )
            else:
                conn.execute(text("ALTER TABLE vouchers ADD COLUMN classification VARCHAR(100) DEFAULT ''"))
        if "details" not in cols:
            if dialect == "postgresql":
                conn.execute(
                    text("ALTER TABLE vouchers ADD COLUMN details VARCHAR(500) NOT NULL DEFAULT ''")
                )
            else:
                conn.execute(text("ALTER TABLE vouchers ADD COLUMN details VARCHAR(500) DEFAULT ''"))

        # Refresh column set after adds
        insp = inspect(engine)
        cols = {c["name"] for c in insp.get_columns("vouchers")}

        if "voucher_line_items" in tables:
            # Copy first line's classification; join all details
            if dialect == "postgresql":
                conn.execute(
                    text(
                        """
                        UPDATE vouchers v SET
                          classification = COALESCE(NULLIF(v.classification, ''), sub.classification, ''),
                          details = COALESCE(
                            NULLIF(v.details, ''),
                            sub.details,
                            ''
                          )
                        FROM (
                          SELECT
                            voucher_id,
                            (ARRAY_AGG(classification ORDER BY id))[1] AS classification,
                            STRING_AGG(NULLIF(details, ''), '; ' ORDER BY id) AS details
                          FROM voucher_line_items
                          GROUP BY voucher_id
                        ) sub
                        WHERE v.id = sub.voucher_id
                        """
                    )
                )
            else:
                rows = conn.execute(
                    text(
                        """
                        SELECT voucher_id, classification, details
                        FROM voucher_line_items
                        ORDER BY id
                        """
                    )
                ).fetchall()
                by_v: dict = {}
                for voucher_id, classification, details in rows:
                    entry = by_v.setdefault(voucher_id, {"classification": "", "details": []})
                    if not entry["classification"] and classification:
                        entry["classification"] = classification
                    if details:
                        entry["details"].append(details)
                for voucher_id, entry in by_v.items():
                    joined = "; ".join(entry["details"])
                    conn.execute(
                        text(
                            """
                            UPDATE vouchers
                            SET classification = CASE
                                  WHEN classification IS NULL OR classification = '' THEN :c
                                  ELSE classification END,
                                details = CASE
                                  WHEN details IS NULL OR details = '' THEN :d
                                  ELSE details END
                            WHERE id = :id
                            """
                        ),
                        {"c": entry["classification"] or "", "d": joined, "id": voucher_id},
                    )

            conn.execute(text("DROP TABLE voucher_line_items"))

        # Drop unused columns (Postgres). SQLite leave orphan cols — rare; rebuild if needed.
        if dialect == "postgresql":
            live_cols = {c["name"] for c in inspect(engine).get_columns("vouchers")}
            for col in ("remarks", "notes", "source_file_url"):
                if col in live_cols:
                    conn.execute(text(f"ALTER TABLE vouchers DROP COLUMN IF EXISTS {col}"))


def ensure_distribution_line_voucher_not_unique(engine: Engine) -> None:
    """Drop the old UNIQUE(voucher_id) constraint on distribution_lines so a
    voucher marked Unpaid again can be re-distributed. SQLite has no
    ALTER TABLE ... DROP CONSTRAINT, so rebuild the table without it."""
    if engine.dialect.name != "sqlite":
        return
    insp = inspect(engine)
    if "distribution_lines" not in insp.get_table_names():
        return
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='distribution_lines'")
        ).fetchone()
        if not row or not row[0]:
            return
        create_sql = row[0]
        if not re.search(r"UNIQUE\s*\(\s*voucher_id\s*\)", create_sql, re.IGNORECASE):
            return

        new_sql = re.sub(r",?\s*UNIQUE\s*\(\s*voucher_id\s*\)", "", create_sql, flags=re.IGNORECASE)
        new_sql = new_sql.replace("distribution_lines", "distribution_lines_new", 1)

        conn.execute(text(new_sql))
        conn.execute(
            text(
                "INSERT INTO distribution_lines_new "
                "(id, distribution_id, employee_id, voucher_id, amount_due, amount_given, shortfall, breakdown) "
                "SELECT id, distribution_id, employee_id, voucher_id, amount_due, amount_given, shortfall, breakdown "
                "FROM distribution_lines"
            )
        )
        conn.execute(text("DROP TABLE distribution_lines"))
        conn.execute(text("ALTER TABLE distribution_lines_new RENAME TO distribution_lines"))


def ensure_distribution_line_reversal_columns(engine: Engine) -> None:
    """Add created_at/reversed_at to distribution_lines, needed to refund cash
    when a paid voucher is flipped back to unpaid."""
    insp = inspect(engine)
    if "distribution_lines" not in insp.get_table_names():
        return
    existing = {c["name"] for c in insp.get_columns("distribution_lines")}
    with engine.begin() as conn:
        if "created_at" not in existing:
            conn.execute(text("ALTER TABLE distribution_lines ADD COLUMN created_at DATETIME"))
            conn.execute(
                text(
                    "UPDATE distribution_lines SET created_at = ("
                    "SELECT distributions.created_at FROM distributions "
                    "WHERE distributions.id = distribution_lines.distribution_id"
                    ") WHERE created_at IS NULL"
                )
            )
        if "reversed_at" not in existing:
            conn.execute(text("ALTER TABLE distribution_lines ADD COLUMN reversed_at DATETIME"))


def drop_cash_counts(engine: Engine) -> None:
    """Remove unused cash_counts table and distributions.cash_count_id FK."""
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    dialect = engine.dialect.name

    with engine.begin() as conn:
        if "distributions" in tables:
            cols = {c["name"] for c in insp.get_columns("distributions")}
            if "cash_count_id" in cols:
                if dialect == "postgresql":
                    # Drop any FK pointing at cash_counts from distributions
                    fks = conn.execute(
                        text(
                            """
                            SELECT conname FROM pg_constraint
                            WHERE conrelid = 'distributions'::regclass
                              AND contype = 'f'
                              AND confrelid = 'cash_counts'::regclass
                            """
                        )
                    ).fetchall()
                    for (conname,) in fks:
                        conn.execute(text(f'ALTER TABLE distributions DROP CONSTRAINT "{conname}"'))
                    conn.execute(text("ALTER TABLE distributions DROP COLUMN cash_count_id"))
                elif dialect == "sqlite":
                    # SQLite: rebuild distributions without cash_count_id
                    conn.execute(
                        text(
                            """
                            CREATE TABLE distributions_new (
                                id CHAR(32) NOT NULL,
                                performed_by_id CHAR(32) NOT NULL,
                                total_distributed NUMERIC(12, 2) NOT NULL,
                                total_shortfall NUMERIC(12, 2) NOT NULL,
                                created_at DATETIME NOT NULL,
                                PRIMARY KEY (id),
                                FOREIGN KEY(performed_by_id) REFERENCES users (id)
                            )
                            """
                        )
                    )
                    conn.execute(
                        text(
                            """
                            INSERT INTO distributions_new
                            (id, performed_by_id, total_distributed, total_shortfall, created_at)
                            SELECT id, performed_by_id, total_distributed, total_shortfall, created_at
                            FROM distributions
                            """
                        )
                    )
                    conn.execute(text("DROP TABLE distributions"))
                    conn.execute(text("ALTER TABLE distributions_new RENAME TO distributions"))
                else:
                    conn.execute(text("ALTER TABLE distributions DROP COLUMN cash_count_id"))

        if "cash_counts" in tables:
            conn.execute(text("DROP TABLE cash_counts"))
