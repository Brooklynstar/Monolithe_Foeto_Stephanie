# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Saisies et téléchargements réels avec Playwright, puis CR via le serveur."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import urlopen

from test_percentiles import DEPOT, administratif, biometrie, dossiers_tests, oracle


class ParcoursNavigateur(unittest.TestCase):
    def test_saisie_exports_json_import_hub_cr_et_calculateur(self):
        with tempfile.TemporaryDirectory(prefix="parcours-percentiles-") as temporaire:
            base = Path(temporaire)
            sortie = Path(os.environ.get("MONOLITHE_TEST_OUTPUT", str(base / "resultats"))).resolve()
            sortie.mkdir(parents=True, exist_ok=True)
            cas = dossiers_tests()
            for d in cas:
                # Tester aussi un dossier réduit à sa saisie biométrique.
                d["administratif"] = None if d["sa"] == 16 else administratif(d["dossier"], d["sa"])
            fichier = base / "cas.json"
            ancien = json.loads((DEPOT / "hub/exemples/26P0123_biometrie_clinique.json").read_text())
            historique = {"dossier": ancien["dossier"], "mesures": ancien["mesures"],
                          "attendus": oracle(biometrie.References().biometrie_clinique,
                                             ancien["terme"]["sa"], ancien["mesures"])}
            fichier.write_text(json.dumps({"cas": cas, "historique": historique}, ensure_ascii=False), encoding="utf-8")
            with socket.socket() as sonde:
                sonde.bind(("127.0.0.1", 0))
                port = sonde.getsockname()[1]
            log = (base / "serveur.log").open("w+")
            with log, subprocess.Popen([sys.executable, "-u", str(DEPOT / "hub/app/serveur.py"),
                                         "--base", str(base / "hub"), "--port", str(port)],
                                        cwd=DEPOT, stdout=log, stderr=subprocess.STDOUT) as proc:
                try:
                    url = f"http://127.0.0.1:{port}"
                    for _ in range(150):
                        if proc.poll() is not None:
                            log.seek(0)
                            self.fail(log.read())
                        try:
                            urlopen(url + "/api/etat", timeout=.2).close()
                            break
                        except OSError:
                            time.sleep(.05)
                    else:
                        self.fail("Serveur non disponible")
                    resultat = subprocess.run(["node", str(DEPOT / "tests/percentiles_browser.cjs"),
                                               str(fichier), url, str(sortie)],
                                              cwd=DEPOT, capture_output=True, text=True, timeout=180)
                    self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
                    print(resultat.stdout.strip())
                finally:
                    proc.terminate()
                    proc.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
