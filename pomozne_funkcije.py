def linspace(a, b, n=100):
    """Generiraj n enakomerno razporejenih točk med a in b"""
    idx = 0
    while idx < n:
        idx += 1
        yield (b - a) * idx / n