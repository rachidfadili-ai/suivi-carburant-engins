# -*- coding: utf-8 -*-
"""Point d'entree : controle des consommations + rapports + dashboard.

    python3 main.py            # analyse data/ -> rapports/
    python3 generer_donnees.py # regenere le jeu de donnees de data/

Sorties :
  rapports/dashboard.html    tableau de bord autonome (aucune connexion)
  rapports/signalements.csv  liste des signalements a revoir
"""

import csv
import os
import sys

from carburant import analyser, lire_config, lire_engins, lire_releves, \
    synthese
from dashboard import generer_dashboard

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
SORTIES = os.path.join(BASE, "rapports")


def main():
    engins = lire_engins(os.path.join(DATA, "engins.csv"))
    releves = lire_releves(os.path.join(DATA, "carburant.csv"))
    config = lire_config(os.path.join(DATA, "config.json"))

    inconnus = sorted({r["engin"] for r in releves} - set(engins))
    if inconnus:
        print("Engins absents de engins.csv : %s" % ", ".join(inconnus))
        return 1

    analyse = analyser(engins, releves)
    kpis = synthese(analyse, config)

    os.makedirs(SORTIES, exist_ok=True)
    dash = generer_dashboard(analyse, kpis,
                             os.path.join(SORTIES, "dashboard.html"),
                             demo=True)
    with open(os.path.join(SORTIES, "signalements.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "engin", "statut", "motif", "litres", "delta",
                    "conso_mesuree"])
        for a in analyse["anomalies"]:
            w.writerow([a["date"], a["engin"], a["statut"], a["motif"],
                        a["litres"], a["delta"], a["ratio"]])

    print("Periode : %s au %s" % analyse["periode"])
    print("Engins suivis : %d" % kpis["nb_engins"])
    print("Litres sur la periode : %.0f L" % kpis["litres_totaux"])
    if kpis.get("conso_moy_h") is not None:
        print("Conso moyenne (horaires) : %.1f L/h" % kpis["conso_moy_h"])
    if kpis.get("conso_moy_km") is not None:
        print("Conso moyenne (camions) : %.1f L/100km" % kpis["conso_moy_km"])
    if kpis.get("cout_estime"):
        print("Cout estime : %.0f %s (prix configurable)"
              % (kpis["cout_estime"], kpis["devise"]))
    print("Signalements a revoir : %d" % kpis["nb_signalements"])
    for a in analyse["anomalies"][:10]:
        print("  %s %-7s %-10s %s" % (a["date"], a["engin"], a["statut"],
                                      a["motif"]))
    if len(analyse["anomalies"]) > 10:
        print("  ... et %d autres (voir rapports/signalements.csv)"
              % (len(analyse["anomalies"]) - 10))
    print("Tableau de bord : %s" % dash)
    return 0


if __name__ == "__main__":
    sys.exit(main())
