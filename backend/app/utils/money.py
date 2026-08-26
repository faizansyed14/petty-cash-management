from decimal import Decimal, ROUND_HALF_UP

FILS = Decimal("100")
TWOPLACES = Decimal("0.01")

DEFAULT_NOTE_DENOMS = ["1000", "500", "200", "100", "50", "20", "10", "5"]
DEFAULT_COIN_DENOMS = ["1", "0.5", "0.25"]


def to_decimal(value) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def to_fils(amount: Decimal | str | int | float) -> int:
    return int((to_decimal(amount) * FILS).to_integral_value(rounding=ROUND_HALF_UP))


def from_fils(fils: int) -> Decimal:
    return (Decimal(fils) / FILS).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def denom_to_fils(denom: str) -> int:
    return to_fils(Decimal(denom))
