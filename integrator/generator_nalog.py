"""Preprosto command-line orodje za ustvarjanje novih nalog."""
import random

import model

DATOTEKA = "primer.json"

integrator = model.Integrator.ustvari_iz_datoteke(DATOTEKA)

# Pridobi zaporedno številko naloge
zaporedna_stevilka = max(int(naloga.zaporedna_stevilka) for naloga in integrator.naloge) + 1
nova_zaporedna_stevilka = input(f"Zapišite številko novo ustvarjene naloge (default={zaporedna_stevilka}) ")
if nova_zaporedna_stevilka.strip():
    zaporedna_stevilka = int(nova_zaporedna_stevilka)


# Pridobi odvedeno funkcijo
niz_funkcije = input("\nZapišite predpis za odvedeno funkcijo: ")
levo, desno = input("\nZapišite območje, ločeno s presledkom: ").split()
levo = float(levo)
desno = float(desno)

odvedena_funkcija = model.Funkcija(niz_funkcije, [levo, desno])

# Pridobi točke
stevilo_tock = int(input("\nZapišite število testnih točk: ").strip())
tocke_za_preverjanje = []
vprasaj = True
for i in range(stevilo_tock):
    if vprasaj:
        podatki = input(f"Testna točka {i + 1}/{stevilo_tock}. Točka (teža=1): ")
        if not podatki.strip():
            # dopolnimo avtomatsko
            vprasaj = False
        else:
            tocka, *teza = podatki.split()
            tocka = float(tocka)
            if teza:
                teza = int(teza[0])
            else:
                teza = 1

    if not vprasaj:
        teza = 1
        tocka = random.uniform(levo, desno)

    tocke_za_preverjanje.append([tocka, teza])

# Besedilo
print("""\nZačnite s pisanjem besedila naloge. Če je prva vrstica prazna, besedila ni. 
Če besedilo je, označite konec pisanja s Ctrl-D.""")
try:
    besedilo = input() + "\n"
    if not besedilo.strip():
        besedilo = besedilo.strip()
        raise EOFError
    while True:
        vrstica = input()
        besedilo += vrstica + "\n"
except EOFError:
    besedilo = besedilo.replace("\n\n", "\n<br>\n")

if besedilo:
    # ustvarimo nov template
    ime_templata = f"naloge/naloga_{zaporedna_stevilka}.html"
    with open("views/"+ime_templata, "w") as f:
        f.write(f"""% rebase('splosna_naloga.html')
<p class="vecje-besedilo">
{besedilo}
</p>
""")

else:
    ime_templata = "splosna_naloga.html"

# Če že obstaja naloga s to številko, jo prepišemo; sicer ustvarimo novo nalogo
if (naloga := integrator.poisci_nalogo(zaporedna_stevilka=zaporedna_stevilka)) is not None:
    integrator.naloge.remove(naloga)

nova_naloga = integrator.naloge.append(model.Naloga(
    ime_templata,
    odvedena_funkcija,
    str(zaporedna_stevilka),
    tocke_za_preverjanje
))

integrator.shrani_v_datoteko(DATOTEKA)