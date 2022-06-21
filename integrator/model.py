import math
import string
from random import choice as random_choice
import json
from datetime import datetime
from hashlib import sha256
import secrets

import funkcije
from pomozne_funkcije import linspace


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
        """Ustvari funkcijo iz neznanih podatkov; lahko je slovar, niz ali Funkcija"""
        if isinstance(podatki, Funkcija):
            return podatki
        if isinstance(podatki, dict):
            return Funkcija(slovar=podatki)
        raise ValueError(f"{podatki} ne ustvari veljavne funkcije.")

    def __str__(self):
        return f"Funkcija {self.niz} na {self.obmocje}"

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

    def narisi_odvod(self, ime_datoteke):
        """Nariši graf odvoda na območju in ga shrani v datoteko."""
        xs = []
        ys = []
        for x in linspace(self.obmocje[0], self.obmocje[1]):
            xs.append(x)
            ys.append(self.izracunaj_odvod(x))

        funkcije.narisi_graf_iz_tock(xs, ys, ime_datoteke)

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

    def oceni_oddajo(self, oddana_funkcija: Funkcija):
        """Oceni oddano funkcijo in vrni številsko vrednost pridobljenih točk."""

        # Ocenjevanje poteka po kriteriju; ta vsebuje pare (meja, vrednost)
        # če se prava funkcija in odvod oddane funkcije v neki
        # točki razlikujeta za manj kot meja, potem dobi oddaja za to točko vrednost% možnih točk
        KRITERIJ = [
            (1e-5, 100),
            (1e-3, 90),
            (1e-1, 60),
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
        for oddaja in self.oddaje:
            if oddaja._id == _id:
                return oddaja
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

        # TODO Polepšaj

        # Imamo dve možni lokaciji funkcij; kot del naloge ali kot oddaja
        # Prvo pogledamo naloge
        for naloga in self.naloge:
            if naloga.odvedena_funkcija._id == id_funkcije:
                return naloga.odvedena_funkcija

        # Sedaj še oddaje
        for uporabnik in self.uporabniki:
            for oddaja in uporabnik.oddaje:
                if oddaja.funkcija._id == id_funkcije:
                    return oddaja.funkcija

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
            for naloga in self.naloge:
                if naloga._id == _id:
                    return naloga
            return None

        return None

    def dodaj_oddajo(self, stevilka_naloge: int, uporabnik: Uporabnik, funkcijski_niz: str):
        """Doda in oceni novo oddajo, vrne novo oddajo.
        Vrne None, če je prišlo do težave (ni naloge, ...)"""
        stevilka_naloge = str(stevilka_naloge)
        naloga = self.poisci_nalogo(stevilka_naloge)
        if naloga is None:
            return None

        funkcija = Funkcija(funkcijski_niz, naloga.odvedena_funkcija.obmocje)
        tocke = naloga.oceni_oddajo(funkcija)
        oddaja = uporabnik.ustvari_oddajo(naloga._id, funkcija, datetime.now(), tocke)
        return oddaja


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

    # funkcija.narisi_graf([-5, 5], "primer.png")
    integrirana.narisi_odvod("primer.png")

