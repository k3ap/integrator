import bottle
import os
import shutil

import pomozne_funkcije
import model


DATOTEKA_Z_BAZO_PODATKOV = "db.json"
MEJA_ZA_NADALJEVANJE = 80   # meja, po kateri so funkcije 'pravilne' in program dovoljuje nadaljevanje
CASOVNI_FORMAT = "%H:%M %-d. %-m. %Y"

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


def napaka(besedilo):
    return bottle.template("napaka.html", napaka=besedilo)


@bottle.route("/uvodna-stran/")
def uvodna_stran():
    if poisci_trenutnega_uporabnika() is not None:
        bottle.redirect("/")
    return bottle.template("uvodna-stran.html")


@bottle.route("/pregled-oddaj/<zaporedna_stevilka:int>/")
def pregled_oddaj(zaporedna_stevilka):
    uporabnik = poisci_trenutnega_uporabnika_ali_redirect()

    oddaje = []
    for oddaja in uporabnik.oddaje:
        naloga = integrator.poisci_nalogo(_id=oddaja.naloga).zaporedna_stevilka
        if naloga != str(zaporedna_stevilka):
            continue

        oddaje.append((
            oddaja._id,
            oddaja.funkcija.niz,
            oddaja.rezultat,
            oddaja.cas_oddaje.strftime(CASOVNI_FORMAT),
        ))

    return bottle.template(
        "pregled_oddaj.html",
        uporabnik=uporabnik,
        oddaje=oddaje,
        meja_za_nadaljevanje=MEJA_ZA_NADALJEVANJE,
        stevilka_naloge=zaporedna_stevilka
    )


@bottle.route("/pregled-oddaje/<id_oddaje>/")
def pregled_oddaje(id_oddaje):
    """Pregled uspešnosti posamične oddaje. gumb_za_naprej pove, če naj ima oddaja gumb za nadaljevanje,
    četudi je morda neuspešna"""
    uporabnik = poisci_trenutnega_uporabnika_ali_redirect()
    oddaja = uporabnik.poisci_oddajo(_id=id_oddaje)
    if oddaja is None:
        bottle.abort(404, "Oddaja ni na voljo.")

    # na strani naj se pokaže gumb za nadaljevanje, če katerakoli uporabnikova oddaja
    # na tej nalogi dosega mejo
    gumb_za_nadaljevanje = uporabnik.je_resil_nalogo(oddaja.naloga, MEJA_ZA_NADALJEVANJE)

    return bottle.template(
        "rezultat_oddaje.html",
        funkcija=oddaja.funkcija,
        rezultat=oddaja.rezultat,
        naloga=integrator.poisci_nalogo(_id=oddaja.naloga),
        meja_za_nadaljevanje=MEJA_ZA_NADALJEVANJE,
        gumb_za_nadaljevanje=gumb_za_nadaljevanje,
        uporabnik=uporabnik
    )


@bottle.route("/")
def index():
    """Glavna stran. Prikaže tabelo rešenih nalog."""
    uporabnik = poisci_trenutnega_uporabnika_ali_redirect()

    # Ustvari seznam parov [naloga, status], kjer je status odvisen od rešitev:
    # če je uporabnik nalogo rešil, je status "zeleno"
    # če je uporabnik nalgoo poskusil, a neuspešno, je status "rdeče"
    # če je uprabnik rešil vse naloge do te, te pa še ni poskusil, je status "modro"
    # sicer je status "sivo"

    def pridobi_status(naloga):
        poskuseno = False
        for oddaja in uporabnik.oddaje:
            if oddaja.naloga == naloga._id:
                poskuseno = True
                if oddaja.rezultat >= MEJA_ZA_NADALJEVANJE:
                    return "zeleno"

        return "rdece" if poskuseno else "sivo"

    naloge = [
        [naloga.zaporedna_stevilka, pridobi_status(naloga)]
        for naloga in integrator.naloge
    ]

    naloge.sort()

    for i, par in enumerate(naloge):
        if par[1] == "sivo" and naloge[i-1][1] == "zeleno":
            par[1] = "modro"

    # To se zgodi, ko uporabnik ni rešil še nobene naloge
    if naloge[0][1] == "sivo":
        naloge[0][1] = "modro"

    vrstice = []
    vrstica = []
    for par in naloge:
        vrstica.append(par)
        if len(vrstica) == 5:
            vrstice.append(vrstica)
            vrstica = []

    if vrstica:
        vrstice.append(vrstica)

    return bottle.template("index.html", uporabnik=uporabnik, vrstice=vrstice)


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
    bottle.redirect("/naloga/1/")


@bottle.route("/graf/<id_funkcije>/")
def graf(id_funkcije):
    """Vrne narisan graf funkcije kot statično datoteko. Slike grafov si shranjuje."""
    funkcija = integrator.poisci_funkcijo(id_funkcije)

    if funkcija is None:
        bottle.abort(404, "Ni take funkcije")

    if not os.path.exists(f"grafi/{id_funkcije}.png"):
        funkcija.narisi_graf(f"grafi/{id_funkcije}.png")

    return bottle.static_file(f"{id_funkcije}.png", "grafi")


@bottle.route("/graf/<id_funkcije>/odvod/")
def graf_odvoda(id_funkcije):
    """Vrne narisan graf odvoda funkcije"""
    funkcija = integrator.poisci_funkcijo(id_funkcije)
    if funkcija is None:
        bottle.abort(404, "Ni take funkcije")

    if not os.path.exists(f"grafi/{id_funkcije}_odvod.png"):
        funkcija.narisi_odvod(f"grafi/{id_funkcije}_odvod.png")

    return bottle.static_file(f"{id_funkcije}_odvod.png", "grafi")


@bottle.get("/naloga/<zaporedna_stevilka:int>/")
def stran_z_nalogo(zaporedna_stevilka):
    """Stran z besedilom naloge"""

    uporabnik = poisci_trenutnega_uporabnika_ali_redirect()

    if zaporedna_stevilka > 1 and \
            not uporabnik.je_resil_nalogo(integrator.poisci_nalogo(zaporedna_stevilka-1)._id, MEJA_ZA_NADALJEVANJE):

        return napaka("Da se lotite naloge, morate rešiti vse naloge pred njo.")

    naloga = integrator.poisci_nalogo(zaporedna_stevilka=zaporedna_stevilka)
    if naloga is None:
        bottle.abort(404, "Ta naloga ne obstaja")
    return bottle.template(
        naloga.ime_templata,
        naloga=naloga,
        prejsnje_oddaje=any(oddaja.naloga == naloga._id for oddaja in uporabnik.oddaje),
        gumb_za_nadaljevanje=uporabnik.je_resil_nalogo(naloga._id, MEJA_ZA_NADALJEVANJE),
        uporabnik=uporabnik
    )


@bottle.post("/naloga/<zaporedna_stevilka:int>/")
def oddaja_naloge(zaporedna_stevilka):
    uporabnik = poisci_trenutnega_uporabnika_ali_redirect()
    if "funkcija" not in bottle.request.forms or not bottle.request.forms["funkcija"]:
        bottle.abort(400, "Ni oddane funkcije.")

    funkcijski_niz = bottle.request.forms["funkcija"]
    oddaja = integrator.dodaj_oddajo(zaporedna_stevilka, uporabnik, funkcijski_niz)

    if oddaja is None:
        # TODO: lepa spletna stran, ki razloži, da imaš napačno sintakso
        bottle.abort(400, "Napaka v funkciji")

    return pregled_oddaje(oddaja._id)


@bottle.route("/static/<datoteka:path>")
def staticne_datoteke(datoteka):
    return bottle.static_file(datoteka, "static")


if __name__ == "__main__":
    debug_nacin = os.environ.get("DEBUG") is not None
    bottle.run(reloader=debug_nacin, debug=debug_nacin)
    integrator.shrani_v_datoteko(DATOTEKA_Z_BAZO_PODATKOV)
