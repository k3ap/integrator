import bottle
import os
import shutil

import pomozne_funkcije
import model


DATOTEKA_Z_BAZO_PODATKOV = "db.json"

# Preberi podatke iz baze

if not os.path.exists(DATOTEKA_Z_BAZO_PODATKOV):
    # Prekopiramo primer
    shutil.copy("primer.json", DATOTEKA_Z_BAZO_PODATKOV)

integrator = model.Integrator.ustvari_iz_datoteke(DATOTEKA_Z_BAZO_PODATKOV)


# Ustvari direktorij za shranjevanje slik grafov, če ta še ne obstaja
if not os.path.exists("grafi/"):
    os.mkdir("grafi")


# Preberi skrivnost ali jo ustvari, če še ne obstaja
if not os.path.exists("SKRIVNOST"):
    with open("SKRIVNOST", "w") as f:
        f.write(pomozne_funkcije.generiraj_skrivnost())

with open("SKRIVNOST") as f:
    SKRIVNOST = f.read()


def poisci_trenutnega_uporabnika():
    """Poišči in vrni Uporabnik objekt, povezan s trenutno prijavljenim uporabnikom. Vrni None, če ga ni."""
    uporabnisko_ime = bottle.request.get_cookie("uporabnisko_ime", secret=SKRIVNOST)
    return integrator.poisci_uporabnika(uporabnisko_ime)


def poisci_trenutnega_uporabnika_ali_redirect(url="/uvodna-stran/"):
    """Pomožna funkcija; če poisci_trenutnega_uporabnika vrne None, ta funkcija napravi redirect."""
    uporabnik = poisci_trenutnega_uporabnika()
    if uporabnik is None:
        bottle.redirect(url)
    return uporabnik


@bottle.route("/uvodna-stran/")
def uvodna_stran():
    if poisci_trenutnega_uporabnika() is not None:
        bottle.redirect("/")
    return bottle.template("uvodna-stran.html")


@bottle.route("/")
def index():
    uporabnik = poisci_trenutnega_uporabnika_ali_redirect()
    return bottle.template("index.html", uporabnik=uporabnik)


@bottle.get("/prijava/")
def stran_za_prijavo(napaka=""):
    return bottle.template("prijava.html", napaka=napaka)


@bottle.post("/prijava/")
def prijava():
    uporabnisko_ime = bottle.request.forms.getunicode("uporabnisko_ime")
    geslo = bottle.request.forms.getunicode("geslo")
    uporabnik = integrator.poisci_uporabnika(uporabnisko_ime)
    if uporabnik is None:
        return stran_za_prijavo(napaka="Ni uporabnika s tem imenom.")
    if not uporabnik.preveri_geslo(geslo):
        return stran_za_prijavo(napaka="Napačno geslo.")
    bottle.response.set_cookie("uporabnisko_ime", uporabnik.uporabnisko_ime, path="/", secret=SKRIVNOST)
    bottle.redirect("/")


@bottle.route("/odjava/")
def odjava():
    uporabnik = poisci_trenutnega_uporabnika()
    if uporabnik is not None:
        bottle.response.delete_cookie("uporabnisko_ime", path="/")
    bottle.redirect("/uvodna-stran/")


@bottle.get("/registracija/")
def stran_za_registracijo(napaka=""):
    return bottle.template("registracija.html", napaka=napaka)


@bottle.post("/registracija/")
def registracija():
    uporabnisko_ime = bottle.request.forms.getunicode("uporabnisko_ime")
    geslo = bottle.request.forms.getunicode("geslo")
    uporabnik = integrator.poisci_uporabnika(uporabnisko_ime)
    if not uporabnisko_ime or not geslo:
        return stran_za_registracijo(napaka="Prazno uporabniško ime ali geslo.")
    if uporabnik is not None:
        return stran_za_registracijo(napaka="Uporabnik s tem imenom že obstaja.")
    integrator.ustvari_uporabnika(uporabnisko_ime, geslo)
    bottle.response.set_cookie("uporabnisko_ime", uporabnisko_ime, path="/", secret=SKRIVNOST)
    bottle.redirect("/")


@bottle.route("/graf/<id_funkcije>/")
def graf(id_funkcije):
    """Vrne narisan graf funkcije kot statično datoteko. Slike grafov si shranjuje."""
    funkcija = integrator.poisci_funkcijo(id_funkcije)

    if funkcija is None:
        bottle.abort(404, "Ni take funkcije")

    if not os.path.exists(f"grafi/{id_funkcije}.png"):
        funkcija.narisi_graf(f"grafi/{id_funkcije}.png")

    return bottle.static_file(f"{id_funkcije}.png", "grafi")


@bottle.get("/naloga/<zaporedna_stevilka:int>")
def stran_z_nalogo(zaporedna_stevilka):
    """Stran z besedilom naloge"""

    uporabnik = poisci_trenutnega_uporabnika_ali_redirect()

    # želimo, da je številka, v bazi pa so kljub temu shranjene kot stringi
    zaporedna_stevilka = str(zaporedna_stevilka)

    naloga = integrator.poisci_nalogo(zaporedna_stevilka=zaporedna_stevilka)
    if naloga is None:
        bottle.abort(404, "Ta naloga ne obstaja")
    return bottle.template(naloga.ime_templata, naloga=naloga)


@bottle.post("/naloga/<zaporedna_stevilka:int>")
def oddaja_naloge(zaporedna_stevilka):
    uporabnik = poisci_trenutnega_uporabnika_ali_redirect()
    if "funkcija" not in bottle.request.forms or not bottle.request.forms["funkcija"]:
        bottle.abort(400, "Ni oddane funkcije.")
    funkcijski_niz = bottle.request.forms["funkcija"]
    rezultat = integrator.dodaj_oddajo(zaporedna_stevilka, uporabnik, funkcijski_niz)
    return bottle.template("rezultat_oddaje.html", predpis_funkcije=funkcijski_niz, rezultat=rezultat)


if __name__ == "__main__":
    debug_nacin = os.environ.get("DEBUG") is not None
    bottle.run(reloader=debug_nacin, debug=debug_nacin)
    integrator.shrani_v_datoteko(DATOTEKA_Z_BAZO_PODATKOV)
