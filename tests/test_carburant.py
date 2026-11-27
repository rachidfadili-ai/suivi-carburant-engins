# -*- coding: utf-8 -*-
"""Tests de la logique de controle carburant (fixtures fabriquees)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from carburant import analyser, lire_engins, lire_releves, synthese  # noqa: E402

BASE = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(BASE, "data")


def engin(code, cpt="h", ref=15.0, tol=15.0):
    return {code: {"code": code, "type": "Test", "chantier": "CH",
                   "compteur": cpt, "conso_ref": ref, "tolerance": tol}}


def releve(code, jour, cpt, litres):
    return {"date": "2026-11-%02d" % jour, "engin": code,
            "compteur": float(cpt), "litres": float(litres)}


def jour_de(analyse, code, jour):
    e = next(x for x in analyse["engins"] if x["code"] == code)
    return next(j for j in e["jours"] if j["j"].endswith("-%02d" % jour))


class TestReglesCompteur(unittest.TestCase):
    def test_compteur_en_baisse_invalide(self):
        a = analyser(engin("X1"), [releve("X1", 1, 100, 0),
                                   releve("X1", 2, 150, 60),
                                   releve("X1", 3, 90, 30)])
        j = jour_de(a, "X1", 3)
        self.assertEqual(j["st"], "INVALIDE")
        self.assertIn("baisse", j["motif"])

    def test_saut_horaire_invalide(self):
        a = analyser(engin("X1"), [releve("X1", 1, 100, 0),
                                   releve("X1", 2, 131, 60)])
        self.assertEqual(jour_de(a, "X1", 2)["st"], "INVALIDE")

    def test_saut_km_invalide(self):
        a = analyser(engin("X1", cpt="km", ref=30),
                     [releve("X1", 1, 1000, 0), releve("X1", 2, 4000, 900)])
        self.assertEqual(jour_de(a, "X1", 2)["st"], "INVALIDE")

    def test_litres_negatifs_invalides(self):
        a = analyser(engin("X1"), [releve("X1", 1, 100, 0),
                                   releve("X1", 2, 110, -5)])
        self.assertEqual(jour_de(a, "X1", 2)["st"], "INVALIDE")


class TestClassification(unittest.TestCase):
    def test_conso_ok(self):
        a = analyser(engin("X1", ref=15.0),
                     [releve("X1", 1, 100, 0), releve("X1", 2, 108, 120)])
        j = jour_de(a, "X1", 2)
        self.assertEqual(j["st"], "OK")
        self.assertAlmostEqual(j["ratio"], 15.0)

    def test_conso_elevee(self):
        # +18% sur une tolerance de 15% -> ELEVE, pas ANORMAL
        a = analyser(engin("X1", ref=15.0),
                     [releve("X1", 1, 100, 0), releve("X1", 2, 110, 177)])
        self.assertEqual(jour_de(a, "X1", 2)["st"], "ELEVE")

    def test_conso_anormale(self):
        # +50% -> ANORMAL (fuite ou vol possible)
        a = analyser(engin("X1", ref=15.0),
                     [releve("X1", 1, 100, 0), releve("X1", 2, 110, 225)])
        j = jour_de(a, "X1", 2)
        self.assertEqual(j["st"], "ANORMAL")
        self.assertIn("fuite", j["motif"])

    def test_conso_impossible_invalide(self):
        a = analyser(engin("X1", ref=15.0),
                     [releve("X1", 1, 100, 0), releve("X1", 2, 110, 500)])
        self.assertEqual(jour_de(a, "X1", 2)["st"], "INVALIDE")

    def test_conso_tres_basse_a_verifier(self):
        a = analyser(engin("X1", ref=15.0),
                     [releve("X1", 1, 100, 0), releve("X1", 2, 110, 30)])
        self.assertEqual(jour_de(a, "X1", 2)["st"], "A_VERIFIER")

    def test_appro_sans_hausse(self):
        a = analyser(engin("X1"), [releve("X1", 1, 100, 0),
                                   releve("X1", 2, 100, 40)])
        j = jour_de(a, "X1", 2)
        self.assertEqual(j["st"], "A_VERIFIER")
        self.assertIn("sans hausse", j["motif"])

    def test_ratio_km_en_l_100km(self):
        a = analyser(engin("X1", cpt="km", ref=30.0),
                     [releve("X1", 1, 1000, 0), releve("X1", 2, 1300, 90)])
        j = jour_de(a, "X1", 2)
        self.assertAlmostEqual(j["ratio"], 30.0)
        self.assertEqual(j["st"], "OK")


class TestPicVsMoyenne(unittest.TestCase):
    def test_pic_detecte(self):
        releves = [releve("X1", 1, 100, 0)]
        cpt = 100
        for j in range(2, 10):
            cpt += 10
            releves.append(releve("X1", j, cpt, 150))  # 15 L/h stables
        cpt += 10
        releves.append(releve("X1", 10, cpt, 375))     # pic a 37.5 L/h
        a = analyser(engin("X1", ref=15.0, tol=15.0), releves)
        j = jour_de(a, "X1", 10)
        self.assertEqual(j["st"], "ANORMAL")
        self.assertIn("pic", j["motif"])

    def test_machine_durablement_haute_pas_de_faux_pic(self):
        # +18% tous les jours (tol 12) : ELEVE partout, jamais ANORMAL
        releves = [releve("X1", 1, 100, 0)]
        cpt = 100
        for j in range(2, 15):
            cpt += 10
            releves.append(releve("X1", j, cpt, 177))
        a = analyser(engin("X1", ref=15.0, tol=12.0), releves)
        statuts = {j["st"] for j in a["engins"][0]["jours"][1:]}
        self.assertEqual(statuts, {"ELEVE"})


class TestTotaux(unittest.TestCase):
    def test_invalides_exclus_des_totaux(self):
        a = analyser(engin("X1"), [releve("X1", 1, 100, 0),
                                   releve("X1", 2, 110, 150),
                                   releve("X1", 3, 90, 500)])
        e = a["engins"][0]
        self.assertEqual(e["litres"], 150.0)   # la ligne invalide est exclue
        self.assertEqual(e["unites"], 10.0)

    def test_synthese(self):
        a = analyser(engin("X1"), [releve("X1", 1, 100, 0),
                                   releve("X1", 2, 110, 150)])
        k = synthese(a, {"prix_litre": 10, "devise": "MAD"})
        self.assertEqual(k["nb_engins"], 1)
        self.assertEqual(k["litres_totaux"], 150.0)
        self.assertEqual(k["cout_estime"], 1500.0)


class TestJeuGenere(unittest.TestCase):
    """Le jeu de donnees genere reste coherent avec les controles."""

    @classmethod
    def setUpClass(cls):
        cls.engins = lire_engins(os.path.join(DATA, "engins.csv"))
        cls.releves = lire_releves(os.path.join(DATA, "carburant.csv"))
        cls.analyse = analyser(cls.engins, cls.releves)

    def test_tous_releves_connus(self):
        self.assertEqual({r["engin"] for r in self.releves} - set(self.engins),
                         set())

    def test_situations_plantees_retrouvees(self):
        par_engin = {}
        for a in self.analyse["anomalies"]:
            par_engin.setdefault(a["engin"], set()).add(a["statut"])
        self.assertIn("ANORMAL", par_engin.get("PEL-07", set()))
        self.assertIn("ANORMAL", par_engin.get("CAM-12", set()))
        self.assertIn("INVALIDE", par_engin.get("CHG-03", set()))
        self.assertIn("A_VERIFIER", par_engin.get("TOM-05", set()))

    def test_signalements_non_vides_mais_limites(self):
        n = len(self.analyse["anomalies"])
        self.assertGreater(n, 10)
        self.assertLess(n, 120)


if __name__ == "__main__":
    unittest.main()
