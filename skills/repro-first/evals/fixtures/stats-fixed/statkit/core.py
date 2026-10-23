def mean(xs):
    xs = list(xs)
    if not xs:
        raise ValueError("mean of empty sequence")
    return sum(xs) / len(xs)


def variance(xs):
    xs = list(xs)
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def median(xs):
    xs = sorted(xs)
    if not xs:
        raise ValueError("median of empty sequence")
    n = len(xs)
    if n % 2 == 0:
        return (xs[n // 2 - 1] + xs[n // 2]) / 2
    return xs[n // 2]
