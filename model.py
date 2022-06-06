import string
from random import choice as random_choice
import json
from datetime import datetime
from hashlib import sha256
import secrets


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
    def __init__(self, niz=None, slovar=None):
        super(Funkcija, self).__init__(slovar=slovar)
        if slovar is not None and "niz" in slovar:
            niz = slovar["niz"]

        if niz is None:
            raise ValueError("Niz ni bil podan.")

        self.niz = niz

    def shrani_v_slovar(self):
        slovar = super(Funkcija, self).shrani_v_slovar()
        slovar.update({
            "niz": self.niz
        })
        return slovar

    @classmethod
    def ustvari_funkcijo(cls, podatki):
        """Ustvari funkcijo iz neznanih podatkov; lahko je slovar, niz ali Funkcija"""
        if isinstance(podatki, Funkcija):
            return podatki
        if isinstance(podatki, str):
            return Funkcija(niz=podatki)
        if isinstance(podatki, dict):
            return Funkcija(slovar=podatki)
        raise ValueError(f"{podatki} ne ustvari veljavne funkcije.")

    def __str__(self):
        return f"Funkcija {self.niz}"


class Naloga(ShranljivObjekt):
    def __init__(self, ime_templata=None, odvedena_funkcija=None, zaporedna_stevilka=None, slovar=None):
        super(Naloga, self).__init__(slovar=slovar)
        if slovar is not None:
            ime_templata = slovar.get("ime_templata", ime_templata)
            odvedena_funkcija = slovar.get("odvedena_funkcija", odvedena_funkcija)
            zaporedna_stevilka = slovar.get("zaporedna_stevilka", zaporedna_stevilka)

        if any(var is None for var in [ime_templata, odvedena_funkcija, zaporedna_stevilka]):
            raise ValueError("Ni dovolj podatkov za izgradnjo Naloge")

        self.ime_templata = ime_templata
        self.zaporedna_stevilka = zaporedna_stevilka
        self.odvedena_funkcija = Funkcija.ustvari_funkcijo(odvedena_funkcija)

    def shrani_v_slovar(self):
        slovar = super(Naloga, self).shrani_v_slovar()
        slovar.update({
            "ime_templata": self.ime_templata,
            "odvedena_funkcija": self.odvedena_funkcija.shrani_v_slovar(),
            "zaporedna_stevilka": self.zaporedna_stevilka
        })
        return slovar

    def __str__(self):
        return f"Naloga {self.zaporedna_stevilka} ({self.ime_templata})"


class Oddaja(ShranljivObjekt):
    def __init__(self, naloga=None, funkcija=None, cas_oddaje=None, rezultat=None, slovar=None):
        super(Oddaja, self).__init__(slovar=slovar)

        if slovar is not None:
            naloga = slovar.get("naloga", naloga)
            funkcija = slovar.get("funkcija", funkcija)
            cas_oddaje = slovar.get("cas_oddaje", cas_oddaje)
            rezultat = slovar.gete("rezultat", rezultat)

        if any(var is None for var in [naloga, funkcija, cas_oddaje, rezultat]):
            raise ValueError("Ni dovolj podatkov za izgradnjo Oddaje")

        self.naloga = naloga  # id naloge (str)
        self.funkcija = Funkcija.ustvari_funkcijo(funkcija)
        self.cas_oddaje = datetime.fromisoformat(cas_oddaje)
        self.rezultat = rezultat  # int (0-100)

    def shrani_v_slovar(self):
        slovar = super(Oddaja, self).shrani_v_slovar()
        slovar.update({
            "naloga": self.naloga,
            "funkcija": self.funkcija.shrani_v_slovar(),
            "cas_oddaje": self.cas_oddaje.isoformat(),
            "rezultat": self.rezultat
        })

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
    def ustvari_uporabnika(cls, uporabnisko_ime, geslo):
        sol = cls.pridobi_sol()
        return Uporabnik(
            oddaje=[],
            uporabnisko_ime=uporabnisko_ime,
            sol=sol,
            razprsitev=sha256((geslo+sol).encode('utf8')).hexdigest()
        )

    def __str__(self):
        return f"Uporabnik {self.uporabnisko_ime}"


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


if __name__ == "__main__":
    primer = Integrator.ustvari_iz_datoteke("primer.json")
    primer.uporabniki.append(Uporabnik.ustvari_uporabnika("janez", "novak"))
    primer.shrani_v_datoteko("prebavljen_primer.json")
