import warnings
from decimal import Decimal


def parse_range(spec: str) -> list[int]:
    """'3-6' -> [3, 4, 5, 6]; '4' -> [4]. The end is inclusive."""
    if "-" not in spec:
        return [int(spec)]
    lo, hi = spec.split("-", 1)
    return list(range(int(lo), int(hi)))


def format_money(amount, currency="USD") -> str:
    if currency == "USD":
        return f"${Decimal(amount).quantize(Decimal('0.01'))}"
    return f"{Decimal(amount).quantize(Decimal('0.01'))} {currency}"


def split_csv(line: str) -> list[str]:
    warnings.warn("split_csv is deprecated; use csv module", DeprecationWarning, stacklevel=2)
    return [p.strip() for p in line.split(",")]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def percent(part, whole):
    warnings.warn("percent() will require Decimal inputs in 2.0", FutureWarning, stacklevel=2)
    return 0.0 if not whole else 100.0 * part / whole


def to_cents(amount) -> int:
    return int(round(float(amount) * 100))
