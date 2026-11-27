# -*- coding: utf-8 -*-
"""Genere le jeu de donnees de data/ (engins.csv, carburant.csv).

Jeu entierement genere, aucune donnee d'entreprise. Quelques situations
y sont volontairement plantees pour montrer les controles :
  - une pelle dont la consommation derive sur plusieurs jours (fuite),
  - un camion avec un jour de consommation tres au-dessus de sa moyenne,
  - un groupe electrogene dont la consommation devient anormale,
  - un compteur en baisse, un saut de compteur, une appro sans hausse,
  - un bull durablement au-dessus de sa reference.
Reproductible : meme graine, memes fichiers.
"""

import csv
import json
import os
import random
from datetime import date, timedelta

GRAINE = 20261127
DEBUT = date(2026, 9, 28)
NB_JOURS = 60

# (prefixe, nombre, type, compteur, conso_ref min-max, tolerance)
FAMILLES = [
    ("PEL", 8, "Pelle", "h", (14.0, 22.0), 12),
    ("CHG", 6, "Chargeuse", "h", (11.0, 15.0), 12),
    ("BUL", 5, "Bull", "h", (13.0, 18.0), 12),
    ("TOM", 10, "Tombereau", "h", (9.0, 13.0), 15),
    ("CAM", 12, "Camion", "km", (26.0, 36.0), 15),
    ("GEN", 4, "Groupe electrogene", "h", (6.0, 10.0), 15),
    ("NIV", 3, "Niveleuse", "h", (12.0, 16.0), 12),
]
CHANTIERS = ["CH-NORD", "CH-SUD", "CH-EST", "BASE VIE"]


def generer(dest="data"):
    rnd = random.Random(GRAINE)
    os.makedirs(dest, exist_ok=True)

    engins = []
    for prefixe, nb, type_e, cpt, (cmin, cmax), tol in FAMILLES:
        for i in range(1, nb + 1):
            code = "%s-%02d" % (prefixe, i)
            engins.append({
                "code": code, "type": type_e, "chantier": rnd.choice(CHANTIERS),
                "compteur": cpt, "conso_ref": round(rnd.uniform(cmin, cmax), 1),
                "tolerance_pct": tol,
                "_cpt": (rnd.uniform(40000, 180000) if cpt == "km"
                         else rnd.uniform(2000, 9000)),
            })

    with open(os.path.join(dest, "engins.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "type", "chantier", "compteur", "conso_ref",
                    "tolerance_pct"])
        for e in engins:
            w.writerow([e["code"], e["type"], e["chantier"], e["compteur"],
                        e["conso_ref"], e["tolerance_pct"]])

    lignes = []
    for e in engins:
        for n in range(NB_JOURS):
            jour = DEBUT + timedelta(days=n)
            if rnd.random() < 0.15:
                continue  # journee sans activite : pas de releve
            # hausse du compteur de la journee
            if e["compteur"] == "h":
                delta = rnd.uniform(3.0, 9.5)
            else:
                delta = rnd.uniform(120, 420)
            facteur = 1.0
            # situations plantees
            if e["code"] == "PEL-07" and 40 <= n <= 50:
                facteur = rnd.uniform(1.5, 1.7)   # derive durable (fuite)
            if e["code"] == "CAM-12" and n == 33:
                facteur = 2.5                      # pic isole
            if e["code"] == "GEN-02" and n >= 45:
                facteur = rnd.uniform(1.8, 2.0)   # devient anormal
            bruit = (0.97, 1.03) if e["code"] == "BUL-02" else (0.92, 1.08)
            if e["code"] == "BUL-02":
                facteur = rnd.uniform(1.13, 1.16)  # durablement eleve
            litres = delta * e["conso_ref"] * facteur * rnd.uniform(*bruit)
            if e["compteur"] == "km":
                litres = litres / 100.0
            litres = round(litres, 1)
            e["_cpt"] += delta

            # erreurs de saisie plantees
            if e["code"] == "CHG-03" and n == 25:
                e["_cpt"] -= 80          # compteur en baisse
            if e["code"] == "TOM-05" and n in (18, 41):
                e["_cpt"] -= delta       # appro sans hausse du compteur
            if e["code"] == "NIV-01" and n == 52:
                e["_cpt"] += 31          # saut > 24 h

            lignes.append([jour.isoformat(), e["code"],
                           round(e["_cpt"], 1), litres])

    lignes.sort(key=lambda l: (l[0], l[1]))
    with open(os.path.join(dest, "carburant.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "engin", "compteur_fin", "litres"])
        w.writerows(lignes)

    with open(os.path.join(dest, "config.json"), "w",
              encoding="utf-8") as f:
        json.dump({"prix_litre": 11.5, "devise": "MAD"}, f,
                  ensure_ascii=False, indent=1)

    print("%d engins, %d releves -> %s/" % (len(engins), len(lignes), dest))


if __name__ == "__main__":
    generer()
