import secrets
import string


def linspace(a, b, n=100):
    """Generiraj n enakomerno razporejenih točk med a in b"""
    idx = 0
    while idx < n:
        idx += 1
        yield a + (b - a) * idx / n


def generiraj_skrivnost():
    """Generira nov string za uporabo kot skrivnost v spletnem vmesniku."""
    ABECEDA = string.ascii_letters + string.digits
    return "".join(secrets.choice(ABECEDA) for __ in range(16))
