# Integrator

Spletna aplikacija za vajo integriranja skozi igro. Osnovna namestitev 
vključuje 20 začetnih nalog, ki vodijo uporabnika skozi delovanje aplikacije
ter mu ponudijo nekaj primerov, v katerih je za uspešno reševanje naloge
potrebna aproksimacija neke funkcije z drugimi.

## Namestitev

Integrator uporablja knjižnice `bottle`, `matplotlib` in `pyparsing`.
Aplikacija je bila ustvarjena in preizkušena na python verziji 3.8.10. 

Za najlažjo inštalacijo je priporočena uporaba virtualnega okolja: 

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uporaba

Po končani namestitvi za uporabo aplikacije poženite skript `pozeni_streznik.sh`,
in obiščite `0.0.0.0:8080`. Nadaljnja navodila za uporabo so vključena v spletni aplikaciji.

Ob prvem zagonu bo aplikacija bazo podatkov z nekaj začetnimi nalogami prebrala 
iz datoteke `primer.json`, ki je za ta namen vključena v repozitoriju. Primer
vključuje tudi uporabnika `resevalec` z geslom `resevalec`, ki ima vse podane 
naloge že rešene, z namenom testiranja avtomatskega generiranja nalog.