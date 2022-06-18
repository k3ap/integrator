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


@bottle.route("/uvodna-stran/")
def uvodna_stran():
    if poisci_trenutnega_uporabnika() is not None:
        bottle.redirect("/")
    return bottle.template("uvodna-stran.html")


@bottle.route("/")
def index():
    uporabnik = poisci_trenutnega_uporabnika()
    if uporabnik is None:
        bottle.redirect("/uvodna-stran/")
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


if __name__ == "__main__":
    debug_nacin = os.environ.get("DEBUG") is not None
    bottle.run(reloader=debug_nacin, debug=debug_nacin)
    integrator.shrani_v_datoteko(DATOTEKA_Z_BAZO_PODATKOV)
