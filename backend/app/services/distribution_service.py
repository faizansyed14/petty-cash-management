"""Cash note/coin distribution algorithm. All math in integer fils."""

from typing import Any, Literal

from app.utils.money import (
    DEFAULT_COIN_DENOMS,
    DEFAULT_NOTE_DENOMS,
    denom_to_fils,
    from_fils,
    to_fils,
)

SortOrder = Literal["ascending", "descending", "voucher_order"]


def _ordered_denoms() -> list[str]:
    all_denoms = DEFAULT_NOTE_DENOMS + DEFAULT_COIN_DENOMS
    return sorted(all_denoms, key=lambda d: denom_to_fils(d), reverse=True)


def _normalize_inventory(inventory: dict[str, Any]) -> dict[str, int]:
    """Flatten nested coins map or flat {denom: count} into flat counts."""
    flat: dict[str, int] = {}
    for key, value in inventory.items():
        if key == "coins" and isinstance(value, dict):
            for ck, cv in value.items():
                flat[str(ck)] = int(cv or 0)
        else:
            flat[str(key)] = int(value or 0)
    return flat


def _flat_breakdown(breakdown: dict[str, int]) -> dict[str, int]:
    """Only include denoms with count > 0, flat (no nested coins)."""
    return {d: c for d, c in breakdown.items() if c > 0}


def calculate_distribution(
    inventory: dict[str, Any],
    payouts: list[dict[str, Any]],
    sort_order: SortOrder = "ascending",
) -> dict[str, Any]:
    inv = _normalize_inventory(inventory)
    starting_total_fils = sum(denom_to_fils(d) * c for d, c in inv.items())
    denoms = _ordered_denoms()

    indexed = list(enumerate(payouts))
    if sort_order == "ascending":
        indexed.sort(key=lambda x: to_fils(x[1]["amount_due"]))
    elif sort_order == "descending":
        indexed.sort(key=lambda x: to_fils(x[1]["amount_due"]), reverse=True)

    lines: list[dict[str, Any]] = []
    total_distributed_fils = 0
    total_shortfall_fils = 0

    for _, payout in indexed:
        remaining = to_fils(payout["amount_due"])
        amount_due_fils = remaining
        line_breakdown: dict[str, int] = {d: 0 for d in denoms}

        for denom in denoms:
            denom_fils = denom_to_fils(denom)
            available = inv.get(denom, 0)
            if available <= 0 or denom_fils <= 0:
                continue
            notes_to_give = min(available, remaining // denom_fils)
            if notes_to_give > 0:
                line_breakdown[denom] = notes_to_give
                remaining -= notes_to_give * denom_fils
                inv[denom] = available - notes_to_give

        given_fils = amount_due_fils - remaining
        shortfall_fils = remaining
        total_distributed_fils += given_fils
        total_shortfall_fils += shortfall_fils

        lines.append(
            {
                "voucher_id": str(payout["voucher_id"]),
                "employee_id": str(payout["employee_id"]),
                "employee_name": payout.get("employee_name", ""),
                "voucher_no": payout.get("voucher_no", ""),
                "amount_due": from_fils(amount_due_fils),
                "amount_given": from_fils(given_fils),
                "shortfall": from_fils(shortfall_fils),
                "breakdown": _flat_breakdown(line_breakdown),
                "insufficient_denominations": shortfall_fils > 0,
            }
        )

    remaining_inventory = _flat_breakdown(inv)
    remaining_total_fils = sum(denom_to_fils(d) * c for d, c in inv.items())

    return {
        "lines": lines,
        "total_distributed": from_fils(total_distributed_fils),
        "total_shortfall": from_fils(total_shortfall_fils),
        "remaining_inventory": remaining_inventory,
        "starting_total": from_fils(starting_total_fils),
        "remaining_total": from_fils(remaining_total_fils),
        "reconciles": remaining_total_fils == starting_total_fils - total_distributed_fils,
    }
