import pyparsing as pp


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


if __name__ == "__main__":
    izraz = "3 + exp((x^9 - 7*x)/2)"
    parser = pridobi_parser()
    print(parser.parseString(izraz))
