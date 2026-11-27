# -*- coding: utf-8 -*-
"""Controle de la consommation de carburant d'un parc d'engins.

Regle d'or : le script SIGNALE les anomalies, il ne corrige jamais la
donnee d'origine. Les lignes INVALIDE ou A_VERIFIER restent visibles
dans les rapports et sont exclues des totaux : la decision finale
reste a l'humain.

Donnees d'entree (data/) :
  engins.csv      code,type,chantier,compteur,conso_ref,tolerance_pct
                  compteur = h (horaire, reference en L/h)
                             ou km (kilometrique, reference en L/100km)
  carburant.csv   date,engin,compteur_fin,litres
                  une ligne par engin et par jour d'activite :
                  compteur de fin de journee et litres approvisionnes.
"""

import csv
import json
import os
from statistics import median

STATUTS = ("OK", "ELEVE", "ANORMAL", "A_VERIFIER", "INVALIDE")

# Saut de compteur au-dela duquel la lecture est invalide (exclue).
SAUT_MAX_H = 24.0        # heures par jour sur un compteur horaire
SAUT_MAX_KM = 2000.0     # km par jour sur un compteur kilometrique
# Au-dela de ce facteur vs la reference, la consommation est
# physiquement impossible : lecture invalide, jamais corrigee.
FACTEUR_IMPOSSIBLE = 3.0
# Pic vs la propre moyenne de l'engin (en plus du depassement de la
# reference) : signale comme consommation anormale.
FACTEUR_PIC = 1.5


def lire_engins(chemin):
    """Lit data/engins.csv -> {code: fiche engin}."""
    engins = {}
    with open(chemin, newline="", encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            code = ligne["code"].strip()
            engins[code] = {
                "code": code,
                "type": ligne["type"].strip(),
                "chantier": ligne["chantier"].strip(),
                "compteur": ligne["compteur"].strip().lower(),  # h | km
                "conso_ref": float(ligne["conso_ref"]),
                "tolerance": float(ligne["tolerance_pct"]),
            }
    return engins


def lire_config(chemin):
    """Lit data/config.json (facultatif) -> dict."""
    if not os.path.exists(chemin):
        return {}
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def lire_releves(chemin):
    """Lit data/carburant.csv -> liste de releves tries par engin/date."""
    releves = []
    with open(chemin, newline="", encoding="utf-8") as f:
        for ligne in csv.DictReader(f):
            releves.append({
                "date": ligne["date"].strip(),
                "engin": ligne["engin"].strip(),
                "compteur": float(ligne["compteur_fin"]),
                "litres": float(ligne["litres"]),
            })
    return releves


def _classer_ratio(ratio, ref, tolerance):
    """Classe une consommation mesuree face a la reference de l'engin.

    Retourne (statut, motif ou None). Ne modifie rien : signale seulement.
    """
    if ratio > ref * FACTEUR_IMPOSSIBLE:
        return ("INVALIDE",
                "consommation physiquement impossible (lecture exclue)")
    ecart = (ratio - ref) / ref * 100.0
    if ecart > 2 * tolerance:
        return ("ANORMAL",
                "consommation anormale : +%.0f%% vs reference "
                "(fuite ou vol possible)" % ecart)
    if ecart > tolerance:
        return ("ELEVE",
                "consommation au-dessus de la reference : +%.0f%%" % ecart)
    if ecart < -2 * tolerance:
        return ("A_VERIFIER",
                "consommation anormalement basse : %.0f%% "
                "(saisie a confirmer)" % ecart)
    return ("OK", None)


def analyser(engins, releves):
    """Analyse les releves engin par engin.

    Retourne {"engins": [...], "anomalies": [...], "jours_parc": [...],
              "periode": (debut, fin)}.
    """
    par_engin = {}
    for r in releves:
        par_engin.setdefault(r["engin"], []).append(r)

    engins_out = []
    anomalies = []

    for code in sorted(par_engin):
        fiche = engins.get(code, {})
        type_cpt = fiche.get("compteur", "h")
        ref = fiche.get("conso_ref")
        tol = fiche.get("tolerance", 15.0)
        lignes = sorted(par_engin[code], key=lambda r: r["date"])

        jours = []
        precedente = None
        for r in lignes:
            statut, motifs = "OK", []
            delta = None
            ratio = None
            if precedente is not None:
                delta = r["compteur"] - precedente
                if delta < 0:
                    statut = "INVALIDE"
                    motifs.append("compteur en baisse (lecture exclue)")
                elif type_cpt == "h" and delta > SAUT_MAX_H:
                    statut = "INVALIDE"
                    motifs.append("saut de compteur > 24 h (lecture exclue)")
                elif type_cpt == "km" and delta > SAUT_MAX_KM:
                    statut = "INVALIDE"
                    motifs.append("saut de compteur > 2000 km "
                                  "(lecture exclue)")
            if r["litres"] < 0:
                statut = "INVALIDE"
                motifs.append("litres negatifs (lecture exclue)")

            if statut != "INVALIDE" and delta is not None and ref:
                if delta > 0 and r["litres"] > 0:
                    if type_cpt == "h":
                        ratio = r["litres"] / delta
                    else:
                        ratio = r["litres"] / delta * 100.0
                    statut, motif = _classer_ratio(ratio, ref, tol)
                    if motif:
                        motifs.append(motif)
                elif r["litres"] > 0 and delta == 0:
                    statut = "A_VERIFIER"
                    motifs.append("approvisionnement sans hausse "
                                  "du compteur")
                elif delta > 0 and r["litres"] == 0:
                    statut = "SANS_APPRO"

            jours.append({
                "j": r["date"], "cpt": r["compteur"], "litres": r["litres"],
                "delta": delta, "ratio": ratio, "st": statut,
                "motif": " ; ".join(motifs),
            })
            precedente = r["compteur"]

        # Pic vs la propre moyenne de l'engin (median des jours mesures).
        ratios_valides = [j["ratio"] for j in jours
                          if j["ratio"] is not None and j["st"] != "INVALIDE"]
        if ref and len(ratios_valides) >= 5:
            base = median(ratios_valides)
            for j in jours:
                if (j["ratio"] is not None and j["st"] != "INVALIDE"
                        and j["ratio"] > base * FACTEUR_PIC
                        and j["ratio"] > ref * (1 + tol / 100.0)):
                    j["st"] = "ANORMAL"
                    j["motif"] = (j["motif"] + " ; " if j["motif"] else "") + \
                        "pic de consommation : %.1f vs sa moyenne %.1f" % (
                            j["ratio"], base)

        # Totaux : lignes invalides exclues, jamais corrigees.
        valides = [j for j in jours if j["st"] != "INVALIDE"]
        mesures = [j for j in valides
                   if j["ratio"] is not None and j["delta"]]
        litres_tot = sum(j["litres"] for j in valides)
        unites_tot = sum(j["delta"] for j in valides if j["delta"])
        conso_moy = None
        if mesures:
            conso_moy = (sum(j["litres"] for j in mesures)
                         / sum(j["delta"] for j in mesures))
            if type_cpt == "km":
                conso_moy *= 100.0
        ecart = None
        if conso_moy is not None and ref:
            ecart = (conso_moy - ref) / ref * 100.0

        gravite = {"OK": 0, "SANS_APPRO": 0, "ELEVE": 1,
                   "A_VERIFIER": 2, "ANORMAL": 3, "INVALIDE": 4}
        pire = "OK"
        for j in jours:
            if gravite.get(j["st"], 0) > gravite.get(pire, 0):
                pire = j["st"]
        compte = {}
        for j in jours:
            compte[j["st"]] = compte.get(j["st"], 0) + 1
        nb_sig = sum(compte.get(s, 0)
                     for s in ("ELEVE", "ANORMAL", "A_VERIFIER", "INVALIDE"))

        for j in jours:
            if j["st"] in ("ELEVE", "ANORMAL", "A_VERIFIER", "INVALIDE"):
                anomalies.append({
                    "date": j["j"], "engin": code, "statut": j["st"],
                    "motif": j["motif"], "litres": j["litres"],
                    "delta": j["delta"], "ratio": j["ratio"],
                })

        engins_out.append({
            "code": code,
            "type": fiche.get("type", "?"),
            "chantier": fiche.get("chantier", "?"),
            "type_compteur": type_cpt,
            "ref": ref, "tolerance": tol,
            "litres": round(litres_tot, 1),
            "unites": round(unites_tot, 1),
            "conso": round(conso_moy, 2) if conso_moy is not None else None,
            "ecart": round(ecart, 1) if ecart is not None else None,
            "statut": pire, "nb_sig": nb_sig,
            "compte": compte, "jours": jours,
        })

    # Litres par jour, parc entier (lignes invalides exclues).
    invalides = {(a["engin"], a["date"]) for a in anomalies
                 if a["statut"] == "INVALIDE"}
    par_jour = {}
    for r in releves:
        if (r["engin"], r["date"]) in invalides:
            continue
        par_jour[r["date"]] = par_jour.get(r["date"], 0.0) + r["litres"]
    jours_parc = [{"j": j, "litres": round(v, 1)}
                  for j, v in sorted(par_jour.items())]

    dates = [r["date"] for r in releves]
    anomalies.sort(key=lambda a: (a["date"], a["engin"]))
    return {
        "engins": engins_out,
        "anomalies": anomalies,
        "jours_parc": jours_parc,
        "periode": (min(dates), max(dates)) if dates else ("", ""),
    }


def synthese(analyse, config=None):
    """Indicateurs globaux pour les cartes du tableau de bord."""
    engins = analyse["engins"]
    litres = sum(e["litres"] for e in engins)
    horaires = [e for e in engins
                if e["type_compteur"] == "h" and e["conso"] is not None]
    kilom = [e for e in engins
             if e["type_compteur"] == "km" and e["conso"] is not None]
    kpis = {
        "nb_engins": len(engins),
        "litres_totaux": round(litres, 0),
        "nb_signalements": len(analyse["anomalies"]),
        "conso_moy_h": round(sum(e["conso"] for e in horaires)
                             / len(horaires), 1) if horaires else None,
        "conso_moy_km": round(sum(e["conso"] for e in kilom)
                              / len(kilom), 1) if kilom else None,
    }
    config = config or {}
    if config.get("prix_litre"):
        kpis["cout_estime"] = round(litres * float(config["prix_litre"]), 0)
        kpis["devise"] = config.get("devise", "")
    return kpis
