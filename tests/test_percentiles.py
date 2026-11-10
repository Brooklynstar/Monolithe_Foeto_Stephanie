# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Calculs, domaines, dossiers historiques et invariants des tables de référence."""
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile

DEPOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPOT / "hub/app"))
import biometrie
import cr
import ingest
import serveur


def oracle(tables, sa, mesures):
    """Lecture indépendante des tables, sans appel au moteur à tester."""
    attendus = {}
    for cle, valeur in mesures.items():
        resultat = {}
        cles = tables["mesures"].get(cle, {})
        if sa is not None and float(sa).is_integer():
            gc = next((r for k, r in tables["GC"].items()
                       if int(k.split("-")[0]) <= sa <= int(k.split("-")[1])), {})
            ma = next((r for r in tables["MA"] if r["s"] == sa), {})
            mb = tables["MB"].get(str(int(sa)), {}) if 12 <= sa <= 20 else {}
            for src, ligne, div in (("GC", gc, 1), ("MA", ma, cles.get("mad", 1)),
                                     ("MB", mb, cles.get("mbd", 1))):
                ref = ligne.get(cles.get(src.lower()), {})
                if valeur is not None and ref.get("m") is not None and ref.get("sd", 0) > 0:
                    zz = (valeur / div - ref["m"]) / ref["sd"]
                    resultat[src] = {"z": zz, "p": 50 * math.erfc(-zz / math.sqrt(2))}
        attendus[cle] = resultat
    return attendus


def dossiers_tests():
    tables = biometrie.References().biometrie_clinique
    mesures = {"masse": 105.421, "pied": 20.451, "bip": 34.4498, "fo": 42.17,
               "main": 17.815, "vt": 169.43, "vc": 117.073, "pc": 121.763,
               "pt": 103.82, "pa": 85.437, "dici": 12}
    cas = []
    for i, sa in enumerate((12, 16, 20, 28, 43, 44, None, 20.5)):
        valeurs = dict(mesures)
        if sa == 20:
            # Z=0,1249, dont le percentile diffère de celui du Z arrondi à 0,12.
            valeurs["bip"] = (4.38 + 0.04 * 0.1249) * 10
        cas.append({"dossier": f"25P{9990 + i}", "sa": sa, "mesures": valeurs,
                    "attendus": oracle(tables, sa, valeurs)})
    return cas


def administratif(numero, sa):
    return {"module": "administratif", "schema_version": "0.3.0", "module_version": "2.1.0",
            "dossier": numero, "operateur": "TEST", "exported_at": "2026-11-09T08:00:00Z",
            "issue": {"terme_sa": sa, "terme_j": 0}}


class Mathematiques(unittest.TestCase):
    def test_points_independants_et_queues(self):
        points = ((0, 50), (1, 84.1344746068543), (-1, 15.8655253931457),
                  (2, 97.7249868051821), (-2, 2.27501319481792),
                  (-8, 6.22096057427178e-14), (-10, 7.61985302416053e-22),
                  (1.959963984540054, 97.5), (-1.959963984540054, 2.5))
        for zz, p in points:
            with self.subTest(z=zz):
                self.assertTrue(math.isclose(biometrie.percentile(zz), p, rel_tol=2e-14, abs_tol=1e-13))
        for zz in (None, "invalide", math.inf, -math.inf, math.nan):
            self.assertIsNone(biometrie.percentile(zz))

    def test_javascript_contre_python_sur_2001_points(self):
        zs = [i / 100 for i in range(-1000, 1001)]
        code = "const fs=require('fs'),vm=require('vm'); const c={};vm.createContext(c);" \
               "vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c);" \
               "const zs=JSON.parse(fs.readFileSync(0,'utf8'));" \
               "console.log(JSON.stringify(zs.map(z=>c.Percentiles.calculer(z))));"
        sortie = subprocess.check_output(["node", "-e", code, str(DEPOT / "hub/app/web/percentiles.js")],
                                         input=json.dumps(zs).encode())
        for zz, p in zip(zs, json.loads(sortie)):
            self.assertAlmostEqual(p, biometrie.percentile(zz), delta=2e-12)

    def test_valeurs_exactes_domaines_et_unites(self):
        refs = biometrie.References()
        cas_tests = dossiers_tests()
        for sa in range(11, 45):
            mesures = cas_tests[1]["mesures"]
            cas_tests.append({"sa": sa, "mesures": mesures,
                              "attendus": oracle(refs.biometrie_clinique, sa, mesures)})
        for cas in cas_tests:
            valeurs = biometrie.calculer(refs, cas["sa"], None, {}, cas["mesures"])
            for cle, sources in cas["attendus"].items():
                r = valeurs.get("bio_" + cle, {})
                for src in ("GC", "MA", "MB"):
                    with self.subTest(sa=cas["sa"], mesure=cle, source=src):
                        if src in sources:
                            self.assertAlmostEqual(r["z_brut_" + src.lower()], sources[src]["z"], places=12)
                            self.assertAlmostEqual(r["percentile_" + src.lower()], sources[src]["p"], places=12)
                            self.assertEqual(r["z_" + src.lower()], round(sources[src]["z"], 2))
                        else:
                            self.assertIsNone(r.get("percentile_" + src.lower()))
        for args in ((1, 1, 0), (1, 1, -1), (None, 1, 1), (math.inf, 1, 1)):
            self.assertIsNone(biometrie.ecart_exact(*args))

    def test_percentile_avant_arrondi_du_z(self):
        cas = dossiers_tests()[2]
        r = biometrie.calculer(biometrie.References(), 20, None, {}, cas["mesures"])["bio_bip"]
        self.assertAlmostEqual(r["percentile_mb"], 54.9698640814085, places=9)
        self.assertGreater(abs(r["percentile_mb"] - biometrie.percentile(r["z_mb"])), 0.1)

    def test_affichage_z_coherent_aux_demi_centiemes(self):
        zs = [3.125, -3.125, 1.005, 2.675, 0, -.0, .0049, -.0049]
        code = "const fs=require('fs'),vm=require('vm'); const c={};vm.createContext(c);" \
               "vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c);" \
               "console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(z=>c.Percentiles.formaterZ(z))));"
        sortie = subprocess.check_output(["node", "-e", code, str(DEPOT / "hub/app/web/percentiles.js")],
                                         input=json.dumps(zs).encode())
        for zz, texte in zip(zs, json.loads(sortie)):
            self.assertEqual(biometrie.zt_externe(zz), texte.replace('.', ',').replace('-', '−') + ' DS')
        self.assertEqual(biometrie.pt(50.125), 'P50,13')


class DossiersHistoriques(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="percentiles-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        ingest.arborescence(self.base)
        self.cx, _ = ingest.ouvrir(self.base / "hub.sqlite")
        self.addCleanup(self.cx.close)
        ingest.migrer(self.cx, DEPOT / "hub/app/migrations", bavard=False)
        self.refs = biometrie.References(self.base)
        self.client = serveur.creer_app(self.base, DEPOT).test_client()

    def ingerer(self, doc):
        brut = json.dumps(doc).encode()
        ingest.ingerer(self.cx, self.base, brut, f"{doc['dossier']}_{doc['module']}.json")
        self.cx.commit()

    def test_ancien_dossier_recalcule_cr_complet_synthese_et_json_archive_intact(self):
        doc = json.loads((DEPOT / "hub/exemples/26P0123_biometrie_clinique.json").read_text())
        self.ingerer(administratif(doc["dossier"], 28))
        self.ingerer(doc)
        attendu = oracle(self.refs.biometrie_clinique, 28, doc["mesures"])
        ctx = cr.contexte(self.cx, doc["dossier"], self.refs, ingest.ORDRE_MODULES)
        self.assertEqual(set(ctx["calc_bio"]), {"masse", "pied", "VT", "VC", "PC"})
        self.assertTrue(all(isinstance(v["ds"], (int, float)) for v in ctx["calc_bio"].values()))
        for ligne in ctx["biometrie"]["lignes"]:
            for src, r in attendu[ligne["cle"]].items():
                self.assertAlmostEqual(ligne["percentile_" + src.lower()], r["p"], places=12)
        for gabarit in ("complet", "synthese"):
            reponse = self.client.post(f"/api/dossiers/{doc['dossier']}/cr", json={"gabarit": gabarit})
            self.assertEqual(reponse.status_code, 200, reponse.text)
            texte = reponse.json["texte"]
            for sources in attendu.values():
                for r in sources.values():
                    # Les CR HTML échappent les signes « < ».
                    from html import unescape
                    self.assertIn(biometrie.pt(r["p"]), unescape(texte))
            sauvegarde = self.client.get(f"/api/cr/{reponse.json['id']}")
            self.assertEqual(sauvegarde.json["texte"], texte)
        self.assertEqual(self.client.get(f"/api/saisie/{doc['dossier']}/biometrie_clinique").json, doc)

    def test_references_prioritaires_sur_percentiles_perimes_et_terme_hors_domaine(self):
        for sa in (16, 28, 44):
            numero = f"TEST-{sa}"
            self.ingerer(administratif(numero, sa))
            self.ingerer({"module": "biometrie_clinique", "schema_version": "0.1.0",
                          "module_version": "1.4.0", "dossier": numero, "operateur": "TEST",
                          "exported_at": "2026-11-09T08:00:00Z", "terme": {"sa": 16},
                          "mesures": {"bip": 34.4498}, "ecarts": {"bip": {"MB": 123}},
                          "ecarts_non_arrondis": {"bip": {"MB": 123}},
                          "percentiles": {"bip": {"MB": 42}}})
            ligne = cr.contexte(self.cx, numero, self.refs, ingest.ORDRE_MODULES)["biometrie"]["lignes"][0]
            if sa == 16:
                self.assertAlmostEqual(ligne["percentile_mb"], 54.9698640814085, places=9)
            else:
                self.assertIsNone(ligne["percentile_mb"])

    def test_sans_tables_ne_pas_inventer_depuis_z_arrondi(self):
        self.ingerer(administratif("TEST-SANS-TABLES", 16))
        doc = {"module": "biometrie_clinique", "schema_version": "0.1.0", "module_version": "1.3.1",
               "dossier": "TEST-SANS-TABLES", "operateur": "TEST", "exported_at": "2026-11-09T08:00:00Z",
               "terme": {"sa": 16}, "mesures": {"bip": 34.4498}, "ecarts": {"bip": {"MB": .12}}}
        self.ingerer(doc)
        self.refs.biometrie_clinique = {}
        ctx = cr.contexte(self.cx, doc["dossier"], self.refs, ingest.ORDRE_MODULES)
        self.assertEqual(ctx["biometrie"]["lignes"][0]["z_mb"], .12)
        self.assertIsNone(ctx["biometrie"]["lignes"][0]["percentile_mb"])
        self.assertNotIn(" · P", ctx["_ds"]("bip"))

    def test_sans_administratif_terme_biometrie_sans_changer_masses(self):
        cas = dossiers_tests()[1]
        doc = {"module": "biometrie_clinique", "schema_version": "0.1.0", "module_version": "1.3.1",
               "dossier": cas["dossier"], "operateur": "TEST", "exported_at": "2026-11-09T08:00:00Z",
               "terme": {"sa": 16}, "mesures": cas["mesures"]}
        self.ingerer(doc)
        ctx = cr.contexte(self.cx, doc["dossier"], self.refs, ingest.ORDRE_MODULES)
        self.assertIsNone(ctx["terme"]["sa"])
        self.assertEqual(ctx["biometrie"]["terme_sa"], 16)
        self.assertEqual(ctx["biometrie"]["terme_source"], "saisie")
        texte, _ = cr.apercu(self.cx, doc["dossier"], "{{ table_biometries_externes() | safe }} {{ _ds('bip') }}",
                            self.refs, ingest.ORDRE_MODULES)
        for ligne in ctx["biometrie"]["lignes"]:
            for src, r in cas["attendus"][ligne["cle"]].items():
                self.assertAlmostEqual(ligne["percentile_" + src.lower()], r["p"], places=12)
                from html import unescape
                self.assertIn(biometrie.pt(r["p"]), unescape(texte))
        self.assertIn("MB +0,12 DS · P54,97", ctx["_ds"]("bip"))


class Presentation(unittest.TestCase):
    def test_colonnes_vides_zero_et_style_cr(self):
        import cr_lumi
        from html import unescape
        html = cr_lumi._table_bio_ext({"bip": {"valeur": 0, "moyenne": 0,
            "z_gc": 0, "z_brut_gc": 0, "percentile_gc": 50}})
        self.assertIn("Moyenne GC", html)
        self.assertIn("Z-score</span> GC", html)
        self.assertIn("P50,00", html)
        self.assertNotIn("Percentile MA", html)
        self.assertNotIn("Percentile MB", html)
        self.assertIn("font-size:11pt", html)
        self.assertIn("font-family:Cambria", html)
        self.assertIn("+0,00 DS", unescape(html))
        self.assertEqual(cr_lumi._table_bio_ext({}), "")


def bloc_table(texte, nom):
    debut = re.search(r"(?:var|const) " + nom + r"\s*=\s*([\[{])", texte).start(1)
    pile = []
    for fin in range(debut, len(texte)):
        if texte[fin] in "[{":
            pile.append(texte[fin])
        elif texte[fin] in "]}":
            pile.pop()
            if not pile:
                return texte[debut:fin + 1]
    raise AssertionError(nom)


class NonRegression(unittest.TestCase):
    def test_tables_externes_et_organes_identiques_aux_references(self):
        # Empreintes des tables existantes, avant toute modification.
        empreintes = {
            "Macro/biometrie_clinique.html": {
                "GC": "65c365adc2124360062a3abcc3992929f1a53deaa07046d5be4f6a5208e4849c",
                "MA": "d2a96fba40cf31f96ebc7c06d0b8cb24ae672c3ebf44b759bd53fb570746f442",
                "MB": "3160ae2c3d0178b215626fb392630e813e64b2e0e50f76a40daad0deca846b18"},
            "hub/calculateur-unifie.html": {
                "GC_M": "6603b7c7bce9320bff8030cae60df4c55898796bd5ba2f498a9e6dc57d72c002",
                "GC_O": "3fd763c032a0c6feb6a370d1981ce6af6b43e9a628b2304c82ce2414517cc9c7",
                "MAR_M": "46bbf85f6f05e332d8f9ac28c22a4e468e0cfecc6eb6d3a05948a76a7b7f6998",
                "MAR_S": "f98d3a1e65af01d882de4d95e2a74d3617509e22f7b850533eceb726ab173e92",
                "MB_B": "a796b7f98c010e0bbb5cc5857e79128c1738a4f154e4a07a80edf107d7e96edc",
                "MB_O": "ea7832e8f49da56abb410bdd2dc1961784c3a2c94705fa0ba25a3ad6c5162294"}}
        for fichier, tables in empreintes.items():
            texte = (DEPOT / fichier).read_text()
            for nom, empreinte in tables.items():
                self.assertEqual(hashlib.sha256(bloc_table(texte, nom).encode()).hexdigest(), empreinte)
        sys.path.insert(0, str(DEPOT / "hub/references"))
        from extraire_modules import litteral
        refs = biometrie.References()
        texte = (DEPOT / "Macro/biometrie_clinique.html").read_text()
        for nom in ("GC", "MA", "MB"):
            self.assertEqual(litteral(texte, nom), refs.biometrie_clinique[nom])

    def test_128_calculs_masses_organes_inchanges(self):
        refs = biometrie.References()
        cas = [biometrie.calculer(refs, sa, g, {c: 20 + i * 7.5 for i, c in enumerate(refs.autopsie["champs"])})
               for sa in range(12, 44) for g in range(4)]
        empreinte = hashlib.sha256(json.dumps(cas, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(empreinte, "e24e322170e243cf3fe1afa30fecd78e5ac022c489f000c8719a373606589627")

    def test_html_autonomes_et_pack_synchronises(self):
        subprocess.run([sys.executable, str(DEPOT / "hub/outils/integrer_percentiles.py"), "--verifier"], check=True)
        self.assertEqual((DEPOT / "Macro/biometrie_clinique.html").read_bytes(),
                         (DEPOT / "pack_telephone/biometrie_clinique.html").read_bytes())
        with zipfile.ZipFile(DEPOT / "pack_telephone.zip") as archive:
            for fichier in (DEPOT / "pack_telephone").iterdir():
                self.assertEqual(archive.read("pack_telephone/" + fichier.name), fichier.read_bytes())


if __name__ == "__main__":
    unittest.main()
