import pyparsing as pp
import math


# Poznane/dovoljene funkcije
FUNKCIJE = {
    "abs": abs,
    "acos": math.acos,
    "acosh": math.acosh,
    "asin": math.asin,
    "asinh": math.asinh,
    "atan": math.atan,
    "atanh": math.atanh,
    "ceil": math.ceil,
    "cos": math.cos,
    "cosh": math.cosh,
    "erf": math.erf,
    "erfc": math.erfc,
    "exp": math.exp,
    "expm1": math.expm1,
    "floor": math.floor,
    "gamma": math.gamma,
    "lgamma": math.lgamma,
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
    "log1p": math.log1p,
    "log2": math.log2,
    "sin": math.sin,
    "sinh": math.sinh,
    "sqrt": math.sqrt,
    "tan": math.tan,
    "tanh": math.tanh,
}

KONSTANTE = {
    "pi": math.pi,
    "tau": math.tau,
    "e": math.e
}

OPERACIJE = {
    "+": lambda a, b: a + b,
    "*": lambda a, b: a * b,
    "-": lambda a, b: a - b,
    "/": lambda a, b: a / b if not math.isclose(b, 0.0) else math.inf,
    "^": lambda a, b: math.pow(a, b)
}


def pridobi_parser():
    """Ustvari in vrni razčlenjevalnik za procesiranje matematičnih izrazov."""

    # Atomi
    stevilka = pp.pyparsing_common.number
    spremenljivka = pp.Word(pp.alphas)
    # Operacije
    plusop = pp.oneOf("+ -")
    multop = pp.oneOf("* /")
    expop = pp.Literal("^")

    # Oklepaji
    levi_oklepaj, desni_oklepaj = map(pp.Suppress, "()")

    # Izraz je definiran rekurzivno, zato potrebujemo Forward()
    izraz = pp.Forward()

    klic_funkcije = pp.Word(pp.alphas, pp.alphanums) + levi_oklepaj + pp.Group(izraz) + desni_oklepaj
    operand = (
        pp.ZeroOrMore(plusop)   # unarni +/-
        + (
            klic_funkcije | spremenljivka | stevilka | pp.Group(levi_oklepaj + izraz + desni_oklepaj)
        )
    )

    # Sloje ustvarimo po precedenci; najglobje v drevesu bodo eksponenti, potem produkti in potem vsote
    # (produkt vklučuje * in /, vsota pa + in -)
    eksponent = pp.Group(operand) + pp.ZeroOrMore(expop + pp.Group(operand))
    produkt = pp.Group(eksponent) + pp.ZeroOrMore(multop + pp.Group(eksponent))
    vsota = pp.Group(produkt) + pp.ZeroOrMore(plusop + pp.Group(produkt))

    izraz <<= vsota

    # TODO: Ugotovi, kako parsati `7x` oziroma `7 x` kot produkt

    return izraz


def predelaj_izraz(izraz: pp.ParseResults):
    """Odstrani odvečne sloje v ParseResults in ga spremeni v list"""
    while isinstance(izraz, pp.ParseResults) and len(izraz) == 1:
        izraz = izraz[0]

    if isinstance(izraz, pp.ParseResults):
        # Trenutno vozlišče je operacija
        return [predelaj_izraz(podizraz) for podizraz in izraz]

    # Trenutno vozlišče je števika ali spremenljivka
    return izraz


def evaluiraj_izraz(izraz: list, x: float):
    """Evaluiraj izraz, predstavljen s seznamom, pri vrednosti x"""

    def rekurzivna_evalvacija(izraz, kontekst):
        """Rekurzivno evaluiraj izraz"""
        if not isinstance(izraz, list):

            if isinstance(izraz, str):
                return kontekst.get(izraz, 0)

            # Če je vse po sreči, je izraz sedaj float ali int
            return izraz

        if len(izraz) == 1:
            # To se načeloma nebi smelo zgoditi
            return rekurzivna_evalvacija(izraz, kontekst)

        elif isinstance(izraz[0], str):

            if izraz[0] in FUNKCIJE:
                argumenti = [rekurzivna_evalvacija(podizraz, kontekst) for podizraz in izraz[1:]]
                return FUNKCIJE[izraz[0]](*argumenti)

            elif izraz[0] in "+-":
                # unarna operacija
                return {"+": 1, "-": -1}[izraz[0]] * rekurzivna_evalvacija(izraz[1], kontekst)

        elif len(izraz) == 3:
            # binarna operacija
            levi = rekurzivna_evalvacija(izraz[0], kontekst)
            desni = rekurzivna_evalvacija(izraz[2], kontekst)
            operacija = izraz[1]
            return OPERACIJE.get(operacija, lambda a, b: 0)(levi, desni)

        else:
            raise ValueError(f"Nepričakovan izraz: {izraz}")

    kontekst = dict(KONSTANTE)
    kontekst["x"] = x
    return rekurzivna_evalvacija(izraz, kontekst)


if __name__ == "__main__":
    izraz = "3 + exp((-x^9 - 7*x)/2)"
    parser = pridobi_parser()
    izraz = parser.parseString(izraz)
    print(izraz)
    izraz = predelaj_izraz(izraz)
    print(izraz)
    for x in [0, 0.1, 1.0, 7]:
        print(f"f({x}) = {evaluiraj_izraz(izraz, x)}")

    import matplotlib.pyplot as plt
    import numpy as np

    xs = np.linspace(-1, 2)
    ys = [evaluiraj_izraz(izraz, x) for x in xs]
    plt.plot(xs, ys)
    plt.show()
