import string
from random import choice as random_choice
import json


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


