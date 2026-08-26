"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-08-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("CASHIER", "MANAGER", "ADMIN", name="role"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_departments_code", "departments", ["code"])

    op.create_table(
        "employees",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("employee_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_code"),
    )
    op.create_index("ix_employees_employee_code", "employees", ["employee_code"])

    op.create_table(
        "vouchers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("voucher_no", sa.String(length=50), nullable=False),
        sa.Column("voucher_date", sa.DateTime(), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=False),
        sa.Column("department_label", sa.String(length=200), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("classification", sa.String(length=100), nullable=False),
        sa.Column("details", sa.String(length=500), nullable=False),
        sa.Column("extraction_source", sa.String(length=100), nullable=True),
        sa.Column("extracted_raw", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "EXTRACTED",
                "VERIFIED",
                "PENDING_PAYMENT",
                "PAID",
                "RECONCILED",
                name="voucherstatus",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voucher_no"),
    )
    op.create_index("ix_vouchers_voucher_no", "vouchers", ["voucher_no"])

    op.create_table(
        "distributions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("performed_by_id", sa.Uuid(), nullable=False),
        sa.Column("total_distributed", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_shortfall", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["performed_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "distribution_lines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("distribution_id", sa.Uuid(), nullable=False),
        sa.Column("employee_id", sa.Uuid(), nullable=False),
        sa.Column("voucher_id", sa.Uuid(), nullable=False),
        sa.Column("amount_due", sa.Numeric(12, 2), nullable=False),
        sa.Column("amount_given", sa.Numeric(12, 2), nullable=False),
        sa.Column("shortfall", sa.Numeric(12, 2), nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["distribution_id"], ["distributions.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["voucher_id"], ["vouchers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("voucher_id"),
    )


def downgrade() -> None:
    op.drop_table("distribution_lines")
    op.drop_table("distributions")
    op.drop_table("vouchers")
    op.drop_table("employees")
    op.drop_table("departments")
    op.drop_table("users")
    sa.Enum(name="voucherstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="role").drop(op.get_bind(), checkfirst=True)
