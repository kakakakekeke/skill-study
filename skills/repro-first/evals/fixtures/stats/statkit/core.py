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
    return xs[len(xs) // 2]
