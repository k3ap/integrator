"""Zbirka orodij za obdelovanje funkcij, vpisanih v matematičnem zapisu - parsing, evalvacija, ..."""

import random

import pyparsing as pp
import math
import matplotlib.pyplot as plt

from pomozne_funkcije import linspace


# Poznane/dovoljene funkcije, ki jih uporabnik lahko zapiše in uporablja
FUNKCIJE = {
    "abs": abs,
    "acos": math.acos,
    "arccos": math.acos,
    "acosh": math.acosh,
    "asin": math.asin,
    "arcsin": math.asin,
    "asinh": math.asinh,
    "atan": math.atan,
    "arctan": math.atan,
    "atanh": math.atanh,
    "ceil": math.ceil,
    "cos": math.cos,
    "cosh": math.cosh,
    "exp": math.exp,
    "floor": math.floor,
    "gamma": math.gamma,
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
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
    "e": math.e,
    # Če uporabnik vpiše kakšno drugo spremenljivko kot x ali zgoraj napisane konstante, bo
    # vrednost te spremenljivke interpretirana kot 0
}

OPERACIJE = {
    "+": lambda a, b: a + b,
    "*": lambda a, b: a * b,
    "-": lambda a, b: a - b,
    "/": lambda a, b: a / b if not math.isclose(b, 0.0) else math.inf,
    "^": lambda a, b: math.pow(a, b)
}

# Minimalni razpon y osi, ki ga ima lahko graf
# Pri aproksimaciji odvoda pride do majhnih napak; tako bi odvod konstantne funkcije
# na narisanem grafu izgledal zelo nekonstanten, če tega ne naredimo
MINIMALNA_VELIKOST_GRAFA = 0.05


def pridobi_parser():
    """Ustvari nov razčlenjevalnik za interpretacijo matematičnih izrazov."""
    stevilka = pp.pyparsing_common.number
    spremenljivka = pp.Word(pp.alphas)

    plusop = pp.oneOf("+ -")
    sgnop = pp.oneOf("+ -")
    multop = pp.oneOf("* /")
    expop = pp.Literal("^")

    levi_oklepaj = pp.Suppress(pp.Literal("(") | pp.Literal("{"))
    desni_oklepaj = pp.Suppress(pp.Literal(")") | pp.Literal("}"))

    izraz = pp.Forward()

    klic_funkcije = pp.Word(pp.alphas) + levi_oklepaj + pp.Group(izraz) + desni_oklepaj
    operand = klic_funkcije | stevilka | spremenljivka

    izraz <<= pp.infixNotation(
        operand,
        [
            (expop, 2, pp.opAssoc.RIGHT),
            (sgnop, 1, pp.opAssoc.RIGHT),
            (multop, 2, pp.opAssoc.LEFT),
            (plusop, 2, pp.opAssoc.LEFT),
        ]
    )

    return izraz


def predelaj_izraz(izraz: pp.ParseResults):
    """Odstrani odvečne sloje v ParseResults in ga spremeni v python list."""

    # Včasih parser kombinira več pp.Group objektov, zaradi česar se v izrazu pojavi več slojev, npr.
    # [[[ ... ]], "+", ...]
    # To želimo odstraniti
    while isinstance(izraz, pp.ParseResults) and len(izraz) == 1:
        izraz = izraz[0]

    if isinstance(izraz, pp.ParseResults):
        # Trenutno vozlišče je operacija
        return [predelaj_izraz(podizraz) for podizraz in izraz]

    # Trenutno vozlišče je števika ali spremenljivka
    return izraz


def ustvari_izraz(niz: str, parser):
    """Ustvari izraz iz niza ter ga vrni že očiščenega."""
    izraz = parser.parseString(niz)
    return predelaj_izraz(izraz)


def evaluiraj_izraz(ociscen_izraz: list, x: float):
    """Evaluiraj izraz, predstavljen s seznamom, pri vrednosti x"""

    def rekurzivna_evalvacija(izraz, kontekst):
        """Rekurzivno evaluiraj izraz"""

        if not isinstance(izraz, list):
            if isinstance(izraz, str):
                return kontekst.get(izraz, 0)

            # Če je vse po sreči, je izraz sedaj float ali int
            return izraz

        # Izraz je sedaj ena ali več levo asociranih binarnih operacij, ali klic funkcije

        # Unarni plus ali minus na začetku (ali tik po oklepaju) se evaluirata drugače kot drugje v izrazu,
        # zato potrebujemo za njiju poseben test
        leva_vrednost = izraz[0]
        indeks = 1  # indeks naslednjega (do sedaj neuporabljenega) dela izraza
        levi_unarni = 1  # +1 ali -1
        while isinstance(leva_vrednost, str) and leva_vrednost in "+-":
            levi_unarni *= {"+": 1, "-": -1}[leva_vrednost]
            leva_vrednost = izraz[indeks]
            indeks += 1

        # Funkcije se parsajo na sledeč način:
        # "3 + cos(x)" --> [3, "+", "cos", "x"]
        if isinstance(leva_vrednost, str) and leva_vrednost in FUNKCIJE:
            leva_vrednost = FUNKCIJE[leva_vrednost](rekurzivna_evalvacija(izraz[indeks], kontekst))
            indeks += 1
        else:
            leva_vrednost = rekurzivna_evalvacija(leva_vrednost, kontekst)

        leva_vrednost *= levi_unarni

        # Ko smo obdelali najbolj levo vrednost, eno po eno obdelamo vse operacije na tem nivoju
        # Levo asocirane operacije z enako precedenco se parsajo na sledeč način:
        # "3 + 2 + 5" --> [3, "+", 2, "+", 5]
        while indeks < len(izraz):
            operator = izraz[indeks]
            indeks += 1
            desna_vrednost = izraz[indeks]
            indeks += 1

            # Tudi desna vrednost je lahko funkcija
            if isinstance(desna_vrednost, str) and desna_vrednost in FUNKCIJE:
                desna_vrednost = FUNKCIJE[desna_vrednost](rekurzivna_evalvacija(izraz[indeks], kontekst))
                indeks += 1
            else:
                desna_vrednost = rekurzivna_evalvacija(desna_vrednost, kontekst)

            # Da simuliramo levo asociranost, samo prepišemo levo vrednost za naslednjo iteracijo
            leva_vrednost = OPERACIJE.get(operator, lambda a, b: 0)(leva_vrednost, desna_vrednost)

        return leva_vrednost

    # Kontekst je skupek vseh vrednosti spremenljivk ob nekem času.
    kontekst = dict(KONSTANTE)
    kontekst["x"] = x
    try:
        return rekurzivna_evalvacija(ociscen_izraz, kontekst)
    except (OverflowError, ZeroDivisionError):
        return math.inf
    except ValueError:
        # Najverjetneje domain error; v takem primeru vse funkcije razširimo na R
        return 0


def narisi_graf_iz_tock(x_tocke, y_tocke, ime_datoteke):
    """Nariši graf iz podanih (x,y) točk, ter ga shrani v datoteko."""
    fig = plt.figure()
    axes = fig.add_subplot()
    axes.plot(x_tocke, y_tocke)

    # Funkcije s konstantnim odvodom izgledajo sila neprijetno, ker matplotlib toliko poveča polje,
    # da lepo vidimo celoten graf; četudi je potem skala na velikosti 1e-10
    # Da to popravimo, na roke povečamo razpon y osi toliko, da je velik vsaj MININALNA_VELIKOST_GRAFA

    spodnja, zgornja = axes.get_ybound()
    if zgornja - spodnja < MINIMALNA_VELIKOST_GRAFA:
        sredina = (zgornja + spodnja) / 2
        axes.set_ybound(sredina - 0.5 * MINIMALNA_VELIKOST_GRAFA, sredina + 0.5 * MINIMALNA_VELIKOST_GRAFA)

    fig.savefig(ime_datoteke)


def narisi_graf(izraz, obmocje, ime_datoteke):
    """Nariši graf funkcije v izrazu na danem območju. Narisano sliko shrani v datoteko."""

    xs = []
    ys = []

    for x in linspace(obmocje[0], obmocje[1]):
        try:
            y = evaluiraj_izraz(izraz, x)
        except (ZeroDivisionError, OverflowError):
            # Overflow se lahko pojavi pri npr. visokih potencah
            y = math.inf

        xs.append(x)
        ys.append(y)

    narisi_graf_iz_tock(xs, ys, ime_datoteke)


def narisi_dvojni_graf_iz_tock(x_tocke, y1_tocke, y2_tocke, naslov1, naslov2, ime_datoteke):
    """Nariši grafa dveh funkcij, združena na enem koordinatnem sistemu. naslov1 in naslov2 označujeta imena
    funkcij na legendi."""
    fig = plt.figure()
    axes = fig.add_subplot()
    axes.plot(x_tocke, y1_tocke, label=naslov1)
    axes.plot(x_tocke, y2_tocke, label=naslov2)
    axes.legend()

    # Po potrebi popravimo y meje
    spodnja, zgornja = axes.get_ybound()
    if zgornja - spodnja < MINIMALNA_VELIKOST_GRAFA:
        sredina = (zgornja + spodnja) / 2
        axes.set_ybound(sredina - 0.5 * MINIMALNA_VELIKOST_GRAFA, sredina + 0.5 * MINIMALNA_VELIKOST_GRAFA)

    fig.savefig(ime_datoteke)


def izracunaj_odvod(izraz, tocka):
    """Izračunaj numerični približek odvoda izraza v dani točki."""

    # Na visokih koordinatah je napaka računanja odvoda večja; to poskusimo rešiti tako,
    # da povečamo razpon točk za računanje
    # Pri mnogo funkcijah to dobro deluje, z nekaterimi izjemami; npr. sinus ali kosinus, kjer
    # večje območje pripomore k večji napaki
    EPS = 1e-6 * max(abs(tocka), 1)

    desno = evaluiraj_izraz(izraz, tocka+EPS)
    levo = evaluiraj_izraz(izraz, tocka-EPS)

    return (desno - levo) / 2 / EPS


def generiraj_funkcijo(globina):
    """Rekurzivno generiraj naključno funkcijo, kjer globina označuje, koliko operacij lahko funkcija vsebuje.
    Vrni niz."""

    if globina <= 1:
        return random.choice((
            "x",
            random.choice(tuple("123456789e") + ("pi",))
        ))

    else:
        if random.randint(0, 1) == 0:
            # izbrana je funkcija
            funkcija = random.choice(list(FUNKCIJE))
            return funkcija + "(" + generiraj_funkcijo(globina-1) + ")"
        else:
            # izbran je operator
            op = random.choice("+-*/^")
            return generiraj_funkcijo(globina-1) + " " + op + " " + generiraj_funkcijo(globina-1)


if __name__ == "__main__":
    izraz = "3 + exp((-x^9 - 7*x)/2)"
    parser = pridobi_parser()
    izraz = parser.parseString(izraz)
    print(izraz)
    izraz = predelaj_izraz(izraz)
    print(izraz)
    for x in [0, 0.1, 1.0, 7]:
        print(f"f({x}) = {evaluiraj_izraz(izraz, x)}")

    narisi_graf(izraz, [1, 10], "test.png")
    print("Narisan graf shranjen v test.png")

    zahteven_izraz = "99999^x"
    zahteven_izraz = ustvari_izraz(zahteven_izraz, parser)
    narisi_graf(zahteven_izraz, [-100, 100], "zahteven_test.png")
    print("Narisan graf shranjen v zahteven_test.png")
