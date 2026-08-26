from decimal import Decimal

from app.services.distribution_service import calculate_distribution


def test_exact_match_plenty_of_notes():
    inventory = {
        "1000": 5, "500": 5, "200": 5, "100": 10, "50": 10, "20": 10, "10": 10, "5": 10,
        "1": 20, "0.5": 20, "0.25": 20,
    }
    payouts = [
        {"voucher_id": "v1", "employee_id": "e1", "amount_due": Decimal("81.00")},
        {"voucher_id": "v2", "employee_id": "e2", "amount_due": Decimal("65.00")},
    ]
    result = calculate_distribution(inventory, payouts, sort_order="ascending")
    assert result["total_shortfall"] == Decimal("0.00")
    assert result["total_distributed"] == Decimal("146.00")
    assert result["reconciles"] is True


def test_eighty_one_includes_one_dirham_coin():
    inventory = {"50": 1, "20": 1, "10": 1, "1": 1}
    payouts = [{"voucher_id": "v1", "employee_id": "e1", "amount_due": Decimal("81.00")}]
    result = calculate_distribution(inventory, payouts)
    assert result["total_distributed"] == Decimal("81.00")
    bd = result["lines"][0]["breakdown"]
    assert bd.get("50") == 1
    assert bd.get("10") == 1 or bd.get("20") == 1  # greedy may vary
    assert bd.get("1") == 1
    assert "coins" not in bd  # flat breakdown only
    assert sum(Decimal(d) * c for d, c in bd.items()) == Decimal("81")


def test_shortfall_case():
    inventory = {"50": 1}
    payouts = [{"voucher_id": "v1", "employee_id": "e1", "amount_due": Decimal("81.00")}]
    result = calculate_distribution(inventory, payouts)
    assert result["lines"][0]["amount_given"] == Decimal("50.00")
    assert result["lines"][0]["shortfall"] == Decimal("31.00")


def test_empty_inventory():
    inventory = {"1000": 0, "1": 0}
    payouts = [{"voucher_id": "v1", "employee_id": "e1", "amount_due": Decimal("10.00")}]
    result = calculate_distribution(inventory, payouts)
    assert result["total_distributed"] == Decimal("0.00")
    assert result["total_shortfall"] == Decimal("10.00")


def test_only_coins_remaining():
    inventory = {"1": 3, "0.5": 2, "0.25": 2}
    payouts = [{"voucher_id": "v1", "employee_id": "e1", "amount_due": Decimal("4.50")}]
    result = calculate_distribution(inventory, payouts)
    assert result["total_distributed"] == Decimal("4.50")
    bd = result["lines"][0]["breakdown"]
    assert bd.get("1") == 3
    assert bd.get("0.5") == 2 or Decimal("0")
    assert sum(Decimal(d) * c for d, c in bd.items()) == Decimal("4.50")
