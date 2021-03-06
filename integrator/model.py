import math
import random
import string
from random import choice as random_choice
import json
from datetime import datetime
from hashlib import sha256
import secrets

import funkcije
from pomozne_funkcije import linspace


def predelaj_niz_za_latex(niz):
    """Polepšaj niz, da bo bolje izgledal v latex-u"""

    # Zamenjave, ki jih program opravi.
    # (ime_funkcije, leva_zamenjava, desna_zamenjava)
    # Izjema tu je zadnji vnos; prazno ime_funkcije pomeni, da bo zamenjal katerekoli oklepaje
    # Dodatni oklepaji okoli vseh funkcij so tam zato, da se `... ^ (funkcija)` pravilno pokaže
    SUBSTITUCIJE = [
        ("abs", "{\\left|", "\\right|}"),
        ("acos", "{\\arccos{(", ")}}"),
        ("arccos", "{\\arccos{(", ")}}"),
        ("asin", "{\\arcsin{(", ")}}"),
        ("arcsin", "{\\arcsin{(", ")}}"),
        ("atan", "{\\arctan{(", ")}}"),
        ("arctan", "{\\arctan{(", ")}}"),
        ("cos", "{\\cos{(", ")}}"),
        ("cosh", "{\\cosh{(", ")}}"),
        ("exp", "{\\exp{(", ")}}"),
        ("log", "{\\log{(", ")}}"),
        ("ln", "{\\ln{(", ")}}"),
        ("sin", "{\\sin{(", ")}}"),
        ("sinh", "{\\sinh{(", ")}}"),
        ("sqrt", "{\\sqrt{", "}}"),
        ("tan", "{\\tan{(", ")}}"),
        ("tanh", "{\\tanh{(", ")}}"),
        ("log10", "{\\log_{10}{(", ")}}"),
        ("log2", "{\\log_2{(", ")}}"),
        ("", "{(", ")}"),
    ]

    # Poiščemo oklepaje, in si označimo, kje se začnejo, končajo, in katera funkcija je pred njimi
    oklepaji = []  # Sklad parov (ime_funkcije, indeks_oklepaja)
    pari_oklepajev = []  # Seznam trojic (ime_funkcije, indeks_levega, indeks_desnega)
    ime_funkcije = ""
    for i, ch in enumerate(niz):
        if ch in string.ascii_letters + string.digits:
            ime_funkcije += ch
        elif ch == "(":
            oklepaji.append((ime_funkcije, i))
            ime_funkcije = ""
        elif ch == ")":
            if not oklepaji:
                # Nekaj je šlo hudo narobe; to se res nebi smelo zgoditi na tej točki
                raise ValueError("Malformed oklepaji v nizu")
            ime, indeks = oklepaji.pop()
            pari_oklepajev.append((ime, indeks, i))
            ime_funkcije = ""
        else:
            ime_funkcije = ""

    # Sedaj zaupamo, da ne manjka noben zaklepaj; sicer bi se parser moral že zdavnaj pritožiti

    zamenjave = []  # (kje se začne zamenjava, koliko za zamenjati, s čim zamenjati)
    for ime, levi, desni in pari_oklepajev:
        for ime_za_zamenjavo, leva_zamenjava, desna_zamenjava in SUBSTITUCIJE:
            if ime_za_zamenjavo == ime:
                break
        else:
            # Če nismo našli prave substitucije, pustimo ime funkcije, kakršno je
            # Primer tega je npr. funkcija floor()
            continue

        zamenjave.append((levi-len(ime), len(ime)+1, leva_zamenjava))
        zamenjave.append((desni, 1, desna_zamenjava))

    zamenjave.sort()
    indeks = 0  # indeks, do izključno katerega smo že obdelali vhodni niz
    rezultat = ""
    for idx, dolzina, zamenjava in zamenjave:
        if indeks < idx:
            rezultat += niz[indeks:idx]
            indeks = idx

        rezultat += zamenjava
        indeks += dolzina

    if indeks != len(niz):
        rezultat += niz[indeks:len(niz)]

    return rezultat


class ShranljivObjekt:
    """Osnovni razred za vse razrede, ki se lahko shranijo v datoteko."""

    # shranjuje "pare"  _id : objekt, da lahko hitro najdemo že ustvarjene objekte
    # in hitro preverimo, če je nek id že zaseden
    ustvarjeni_objekti = {}

    # znaki, ki jih dovoljujemo v idjih
    ZNAKI_ZA_ID = string.ascii_letters + string.digits

    def __init__(self, _id=None, slovar=None):
        """Konstruktor ima dve funkciji - lahko naredi objekt iz slovarja, ali čisto na novo."""
        if slovar is not None and '_id' in slovar:
            _id = slovar['_id']

        if _id is None:
            self._id = self.pridobi_nov_id()
        else:
            self._id = _id

        self.ustvarjeni_objekti[self._id] = self

    @classmethod
    def generiraj_id(cls):
        """Ustvari nov id - niz dolžine 16, ki pripada vsakemu shranljivemu objektu.
        Metoda *ne* preverja, če so idji unikatni - za to se uporablja ShranljivObjekt.pridobi_nov_id"""
        nov_id = ""
        for __ in range(16):
            nov_id += random_choice(cls.ZNAKI_ZA_ID)
        return nov_id

    @classmethod
    def pridobi_nov_id(cls):
        """Pridobi nov unikaten id."""
        while (nov_id := cls.generiraj_id()) in cls.ustvarjeni_objekti:
            pass
        return nov_id

    def shrani_v_slovar(self):
        return {
            "_id": self._id
        }

    def shrani_v_datoteko(self, ime_datoteke: str):
        with open(ime_datoteke, "w") as f:
            json.dump(self.shrani_v_slovar(), f)

    @classmethod
    def ustvari_iz_datoteke(cls, ime_datoteke: str):
        with open(ime_datoteke) as f:
            return cls(slovar=json.load(f))


class Funkcija(ShranljivObjekt):

    # Parser za spremembo niza v 'pravo' funkcijo potrebujemo konstruirati le enkrat
    _parser = None

    def __init__(self, niz=None, obmocje=None, slovar=None):
        super(Funkcija, self).__init__(slovar=slovar)
        if slovar is not None:
            if "niz" in slovar:
                niz = slovar["niz"]
            if "obmocje" in slovar:
                obmocje = list(slovar["obmocje"])

        if any(var is None for var in [niz, obmocje]):
            raise ValueError("Niz ni bil podan.")

        self.niz = niz
        self.obmocje = obmocje

        # Izraz, ki ga lahko evaluiramo
        self._izraz = None

    def shrani_v_slovar(self):
        slovar = super(Funkcija, self).shrani_v_slovar()
        slovar.update({
            "niz": self.niz,
            "obmocje": self.obmocje
        })
        return slovar

    @classmethod
    def ustvari_funkcijo(cls, podatki):
        """Ustvari funkcijo iz neznanih podatkov; lahko je slovar ali Funkcija"""
        if isinstance(podatki, Funkcija):
            return podatki
        if isinstance(podatki, dict):
            return Funkcija(slovar=podatki)
        raise ValueError(f"{podatki} ne ustvari veljavne funkcije.")

    def __str__(self):
        return f"Funkcija {self.niz} na {self.obmocje}"

    @property
    def niz_latex(self):
        """Vrni niz funkcije, polepšan za LaTeX izpis."""
        return predelaj_niz_za_latex(self.niz)

    @classmethod
    def _pridobi_parser(cls):
        """Pridobi parser za spremembo niza v izraz."""
        if cls._parser is None:
            cls._parser = funkcije.pridobi_parser()
        return cls._parser

    @property
    def izraz(self):
        """Pridobi izraz, ki pripada funkciji"""
        if self._izraz is None:
            self._izraz = funkcije.ustvari_izraz(self.niz, self._pridobi_parser())
        return self._izraz

    def narisi_graf(self, ime_datoteke):
        """Nariši graf funkcije na podanem območju in ga shrani v datoteko"""
        funkcije.narisi_graf(self.izraz, self.obmocje, ime_datoteke)

    def izracunaj_odvod(self, tocka):
        """Izračunaj približek odvoda v točki."""
        return funkcije.izracunaj_odvod(self.izraz, tocka)

    def evaluiraj(self, x):
        """Evaluiraj funkcijo v x."""
        return funkcije.evaluiraj_izraz(self.izraz, x)


class Naloga(ShranljivObjekt):
    def __init__(
            self,
            ime_templata=None,
            odvedena_funkcija=None,
            zaporedna_stevilka=None,
            tocke_za_preverjanje=None,
            slovar=None):

        super(Naloga, self).__init__(slovar=slovar)
        if slovar is not None:
            ime_templata = slovar.get("ime_templata", ime_templata)
            odvedena_funkcija = slovar.get("odvedena_funkcija", odvedena_funkcija)
            zaporedna_stevilka = slovar.get("zaporedna_stevilka", zaporedna_stevilka)
            tocke_za_preverjanje = slovar.get("tocke_za_preverjanje", tocke_za_preverjanje)

        if any(var is None for var in [ime_templata, odvedena_funkcija, zaporedna_stevilka, tocke_za_preverjanje]):
            raise ValueError("Ni dovolj podatkov za izgradnjo Naloge")

        self.ime_templata = ime_templata
        self.zaporedna_stevilka = zaporedna_stevilka
        self.odvedena_funkcija = Funkcija.ustvari_funkcijo(odvedena_funkcija)

        # tocke_za_preverjanje je seznam parov (x, teza), kjer je x koordinata, teza pa pove, kolikšen delež
        # vseh odstotkov pripada tej točki
        self.tocke_za_preverjanje = tocke_za_preverjanje

    def shrani_v_slovar(self):
        slovar = super(Naloga, self).shrani_v_slovar()
        slovar.update({
            "ime_templata": self.ime_templata,
            "odvedena_funkcija": self.odvedena_funkcija.shrani_v_slovar(),
            "zaporedna_stevilka": self.zaporedna_stevilka,
            "tocke_za_preverjanje": self.tocke_za_preverjanje,
        })
        return slovar

    def __str__(self):
        return f"Naloga {self.zaporedna_stevilka} ({self.ime_templata})"

    def __lt__(self, o):
        return int(self.zaporedna_stevilka) < int(o.zaporedna_stevilka)

    def oceni_oddajo(self, oddana_funkcija: Funkcija):
        """Oceni oddano funkcijo in vrni številsko vrednost pridobljenih točk."""

        # Ocenjevanje poteka po kriteriju; ta vsebuje pare (meja, vrednost)
        # če se prava funkcija in odvod oddane funkcije v neki
        # točki razlikujeta za manj kot meja, potem dobi oddaja za to točko vrednost% možnih točk
        KRITERIJ = [
            (1e-5, 100),
            (1e-3, 90),
            (1e-1, 80),
            (1e0, 30),
            (1e1, 10),
            (math.inf, 0)
        ]

        skupna_teza = sum(teza for __, teza in self.tocke_za_preverjanje)
        skupne_tocke = 0

        for x, teza in self.tocke_za_preverjanje:
            y1 = self.odvedena_funkcija.evaluiraj(x)
            y2 = oddana_funkcija.izracunaj_odvod(x)

            if y1 == y2:
                # primer, ko sta obe števili neskončni, moramo obravnavati posebaj
                skupne_tocke += teza
                continue

            delta = float(abs(y1 - y2))

            if math.isinf(delta) or math.isnan(delta):
                # Neskončna razlika pomeni 0 točk
                continue

            for meja, vrednost in KRITERIJ:
                if delta < meja * max(abs(y1) + abs(y2), 1):
                    skupne_tocke += teza * vrednost / 100
                    break

        return round(skupne_tocke * 100 / skupna_teza)


class Oddaja(ShranljivObjekt):
    def __init__(self, naloga=None, funkcija=None, cas_oddaje=None, rezultat=None, slovar=None):
        super(Oddaja, self).__init__(slovar=slovar)

        if slovar is not None:
            naloga = slovar.get("naloga", naloga)
            funkcija = slovar.get("funkcija", funkcija)
            cas_oddaje = slovar.get("cas_oddaje", cas_oddaje)
            rezultat = slovar.get("rezultat", rezultat)

        if any(var is None for var in [naloga, funkcija, cas_oddaje, rezultat]):
            raise ValueError("Ni dovolj podatkov za izgradnjo Oddaje")

        self.naloga = naloga  # id naloge (str)
        self.funkcija = Funkcija.ustvari_funkcijo(funkcija)
        self.cas_oddaje = datetime.fromisoformat(cas_oddaje) if isinstance(cas_oddaje, str) else cas_oddaje
        self.rezultat = rezultat  # int (0-100)

    def shrani_v_slovar(self):
        slovar = super(Oddaja, self).shrani_v_slovar()
        slovar.update({
            "naloga": self.naloga,
            "funkcija": self.funkcija.shrani_v_slovar(),
            "cas_oddaje": self.cas_oddaje.isoformat(),
            "rezultat": self.rezultat
        })
        return slovar

    def __str__(self):
        return f"Oddaja za nalogo {self.naloga} s funkcijo {self.funkcija}"


class Uporabnik(ShranljivObjekt):
    def __init__(self, oddaje=None, uporabnisko_ime=None, sol=None, razprsitev=None, slovar=None):
        super(Uporabnik, self).__init__(slovar=slovar)

        if slovar is not None:
            if "oddaje" in slovar:
                oddaje = [Oddaja(slovar=oddaja) for oddaja in slovar["oddaje"]]
            uporabnisko_ime = slovar.get("uporabnisko_ime", uporabnisko_ime)
            sol = slovar.get("sol", sol)
            razprsitev = slovar.get("razprsitev", razprsitev)

        if any(var is None for var in [oddaje, uporabnisko_ime, sol, razprsitev]):
            raise ValueError("Ni dovolj podatkov za izgradnjo Uporabnika")

        self.oddaje = oddaje
        self.uporabnisko_ime = uporabnisko_ime
        self.sol = sol   # 16 bajtov, shranjenih v hex
        self.razprsitev = razprsitev   # sha-256 hash, shranjen v hex, od geslo+sol

    def shrani_v_slovar(self):
        slovar = super(Uporabnik, self).shrani_v_slovar()
        slovar.update({
            "oddaje": [oddaja.shrani_v_slovar() for oddaja in self.oddaje],
            "uporabnisko_ime": self.uporabnisko_ime,
            "sol": self.sol,
            "razprsitev": self.razprsitev
        })
        return slovar

    @classmethod
    def pridobi_sol(cls):
        """Ustvari sol"""
        return secrets.token_hex(16)

    @classmethod
    def razprsi(cls, geslo, sol):
        """Ustvari razprsitev iz gesla in soli."""
        return sha256((geslo+sol).encode('utf8')).hexdigest()

    @classmethod
    def ustvari_uporabnika(cls, uporabnisko_ime, geslo):
        sol = cls.pridobi_sol()
        return Uporabnik(
            oddaje=[],
            uporabnisko_ime=uporabnisko_ime,
            sol=sol,
            razprsitev=Uporabnik.razprsi(geslo, sol)
        )

    def __str__(self):
        return f"Uporabnik {self.uporabnisko_ime}"

    def preveri_geslo(self, geslo: str):
        """Vrne True, če je geslo pravilno za tega uporabnika, in False sicer."""
        return self.razprsitev == self.razprsi(geslo, self.sol)

    def nastavi_geslo(self, novo_geslo: str):
        """Nastavi geslo na novo vrednost"""
        self.razprsitev = Uporabnik.razprsi(novo_geslo, self.sol)

    def ustvari_oddajo(self, id_naloge, oddana_funkcija, cas_oddaje, rezultat):
        """Ustvari novo oddajo in jo dodaj v svoj seznam. Vrni novo oddajo."""
        self.oddaje.append(Oddaja(
            id_naloge,
            oddana_funkcija,
            cas_oddaje,
            rezultat
        ))
        return self.oddaje[-1]

    def poisci_oddajo(self, _id):
        """Poišči oddajo ali vrni None, če ne obstaja"""
        objekt = Oddaja.ustvarjeni_objekti.get(_id, None)
        if isinstance(objekt, Oddaja) and objekt in self.oddaje:
            return objekt
        return None

    def je_resil_nalogo(self, naloga: str, meja: int):
        """Vrne True, če je vsaj ena uporabnikova oddaja pri nalogi dobila višji rezultat od meje."""
        return any(oddaja.naloga == naloga and oddaja.rezultat >= meja for oddaja in self.oddaje)


class Integrator(ShranljivObjekt):
    def __init__(self, naloge=None, uporabniki=None, slovar=None):
        super(Integrator, self).__init__(slovar=slovar)
        if slovar is not None:
            if "naloge" in slovar:
                naloge = [Naloga(slovar=naloga) for naloga in slovar["naloge"]]
            if "uporabniki" in slovar:
                uporabniki = [Uporabnik(slovar=uporabnik) for uporabnik in slovar["uporabniki"]]

        if any(var is None for var in [naloge, uporabniki]):
            raise ValueError("Ni dovolj podatkov za izgradnjo Integratorja")

        self.naloge = naloge
        self.uporabniki = uporabniki

    def shrani_v_slovar(self):
        slovar = super(Integrator, self).shrani_v_slovar()
        slovar.update({
            "naloge": [naloga.shrani_v_slovar() for naloga in self.naloge],
            "uporabniki": [uporabnik.shrani_v_slovar() for uporabnik in self.uporabniki]
        })
        return slovar

    def poisci_uporabnika(self, uporabnisko_ime: str):
        """Poišči in vrni uporabnika z podanim imenom. Če tak uporabnik ne obstaja, vrni None"""
        for up in self.uporabniki:
            if up.uporabnisko_ime == uporabnisko_ime:
                return up
        return None

    def ustvari_uporabnika(self, uporabnisko_ime, geslo):
        """Ustvari novega uporabnika."""
        self.uporabniki.append(Uporabnik.ustvari_uporabnika(uporabnisko_ime, geslo))

    def poisci_funkcijo(self, id_funkcije):
        """Poišči in vrni funkcijo z danim ID-jem. Če ne obstaja, vrni None."""

        objekt = Funkcija.ustvarjeni_objekti.get(id_funkcije, None)

        if isinstance(objekt, Funkcija):
            return objekt

        return None

    def poisci_nalogo(self, zaporedna_stevilka=None, _id=None):
        """Vrni nalogo z dano zaporedno številko oz. ID-jem, ali None, če taka naloga ne obstaja."""
        if zaporedna_stevilka is not None:
            zaporedna_stevilka = str(zaporedna_stevilka)
            for naloga in self.naloge:
                if naloga.zaporedna_stevilka == zaporedna_stevilka:
                    return naloga
            return None

        if _id is not None:
            objekt = Naloga.ustvarjeni_objekti.get(_id, None)
            if isinstance(objekt, Naloga):
                return objekt
            return None

        return None

    def dodaj_oddajo(self, stevilka_naloge: int, uporabnik: Uporabnik, funkcijski_niz: str):
        """Doda in oceni novo oddajo, vrne novo oddajo.
        Vrne None, če je prišlo do težave (ni naloge, ...)"""
        stevilka_naloge = str(stevilka_naloge)
        naloga = self.poisci_nalogo(stevilka_naloge)
        if naloga is None:
            return None

        try:
            funkcija = Funkcija(funkcijski_niz, naloga.odvedena_funkcija.obmocje)
            tocke = naloga.oceni_oddajo(funkcija)
        except Exception:
            return None

        oddaja = uporabnik.ustvari_oddajo(naloga._id, funkcija, datetime.now(), tocke)
        return oddaja

    def poisci_oddaje_za_nalogo(self, id_naloge):
        """Poišči vse oddaje, ki pripadajo nalogi. Vrača pare (oddaja, uporabnik)"""
        for uporabnik in self.uporabniki:
            for oddaja in uporabnik.oddaje:
                if oddaja.naloga == id_naloge:
                    yield oddaja, uporabnik

    def ustvari_nakljucno_nalogo(self, zaporedna_stevilka):
        """Ustvari novo, naključno generirano nalogo."""

        # Koliko je minimalna in koliko maksimalna globina funkcije
        KOMPLEKSNOST = (2, 4)

        obmocje = [-1, 1]
        niz_funkcije = funkcije.generiraj_funkcijo(random.randint(*KOMPLEKSNOST))
        funkcija = Funkcija(niz_funkcije, obmocje)

        # Poskusimo narisati graf; če nam to ne uspe (npr. če smo poskusili izračunali atanh(6)), zgeneriramo funkcijo
        # znova

        funkcija_deluje = False
        while not funkcija_deluje:
            try:
                funkcija.narisi_graf(f"grafi/{funkcija._id}.png")
            except ValueError:  # math domain error
                niz_funkcije = funkcije.generiraj_funkcijo(random.randint(*KOMPLEKSNOST))
                funkcija = Funkcija(niz_funkcije, obmocje)
            else:
                funkcija_deluje = True

        self.naloge.append(Naloga(
            "splosna_naloga.html",
            funkcija,
            str(zaporedna_stevilka),
            [(x, 1) for x in funkcije.linspace(*obmocje, 20)]
        ))
        return self.naloge[-1]


def graf_naloge_in_odvoda_oddaje(naloga: Naloga, oddaja: Oddaja, ime_datoteke: str):
    """Nariši graf v nalogi podane funkcije in odvoda oddane funkcije v istem koordinatnem sistemu."""
    xs = []
    ys1 = []
    ys2 = []

    for x in funkcije.linspace(naloga.odvedena_funkcija.obmocje[0], naloga.odvedena_funkcija.obmocje[1]):
        try:
            y1 = naloga.odvedena_funkcija.evaluiraj(x)
        except (ZeroDivisionError, OverflowError):
            y1 = math.inf

        try:
            y2 = oddaja.funkcija.izracunaj_odvod(x)
        except (ZeroDivisionError, OverflowError):
            y2 = math.inf

        xs.append(x)
        ys1.append(y1)
        ys2.append(y2)

    funkcije.narisi_dvojni_graf_iz_tock(
        xs, ys1, ys2, "Podana funkcija", "Odvod oddane funkcije", ime_datoteke
    )


if __name__ == "__main__":
    primer = Integrator.ustvari_iz_datoteke("primer.json")
    primer.uporabniki.append(Uporabnik.ustvari_uporabnika("janez", "novak"))
    funkcija = Funkcija("2*x", [-5, 5])
    integrirana = Funkcija("x^2 + 3", [-5, 5])
    primer.naloge.append(Naloga("primer.html", funkcija, 1))
    primer.uporabniki[0].oddaje.append(Oddaja(
        primer.naloge[0]._id,
        integrirana,
        "2022-03-22 03:33:22",
        100
    ))
    primer.shrani_v_datoteko("prebavljen_primer.json")


