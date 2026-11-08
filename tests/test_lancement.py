# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Tests réseau avec bases jetables, sans ouvrir le navigateur du poste.

    hub/app/.venv/bin/python -m unittest discover -s tests -v
"""
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.request import urlopen


APP = Path(__file__).resolve().parents[1] / "hub" / "app"
# Le vrai serveur tourne ; seul l'appel au navigateur est enregistré.
DEMARRER = """
import pathlib, runpy, socket, sys, webbrowser
from urllib.parse import urlsplit
trace = pathlib.Path(sys.argv.pop(1))
sys.argv.pop(0)
def ouvrir(url):
    cible = urlsplit(url)
    with socket.create_connection((cible.hostname, cible.port), timeout=1):
        pass
    trace.write_text(url, encoding='utf-8')
    return True
webbrowser.open = ouvrir
runpy.run_path(sys.argv[0], run_name='__main__')
"""


class Lancement(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="monolithe test ")
        self.addCleanup(self.temp.cleanup)
        self.racine = Path(self.temp.name)

    def lancer(self, nom, *options):
        # Deux vrais dossiers de code, avec leurs bases distinctes.
        app = self.racine / nom / "hub" / "app"
        shutil.copytree(APP, app, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
        trace = app.parent / "navigateur.txt"
        log = (app.parent / "serveur.log").open("w+")
        self.addCleanup(log.close)
        proc = subprocess.Popen(
            [sys.executable, "-u", "-c", DEMARRER, str(trace),
             str(app / "serveur.py"), *options],
            cwd=self.racine, stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONPATH": str(app)},
        )

        def arreter():
            if proc.poll() is None:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
        self.addCleanup(arreter)
        return proc, trace, app.parent, log

    def attendre(self, proc, url, log):
        limite = time.monotonic() + 15
        while time.monotonic() < limite and proc.poll() is None:
            try:
                with urlopen(url, timeout=0.3) as reponse:
                    return reponse.read()
            except OSError:
                time.sleep(0.05)
        log.seek(0)
        self.fail(f"Serveur indisponible : {url}\n{log.read()}")

    def test_ports_5005_5006_bases_distinctes_et_port_occupe(self):
        for port in (5005, 5006):
            with socket.socket() as sonde:
                try:
                    sonde.bind(("127.0.0.1", port))
                except OSError:
                    self.skipTest(f"port {port} déjà utilisé par un service extérieur au test")
        original, _, base1, log1 = self.lancer("original", "--port", "5005")
        self.attendre(original, "http://127.0.0.1:5005/", log1)
        stephanie, trace, base2, log2 = self.lancer("Stéphanie avec espaces", "--ouvrir-navigateur")
        self.attendre(stephanie, "http://127.0.0.1:5006/", log2)
        self.assertEqual(trace.read_text(), "http://127.0.0.1:5006/")
        for proc, base, port, log in ((original, base1, 5005, log1),
                                      (stephanie, base2, 5006, log2)):
            etat = json.loads(self.attendre(proc, f"http://127.0.0.1:{port}/api/etat", log))
            self.assertEqual(etat["racine"], str(base))
            self.assertTrue((base / "hub.sqlite").is_file())
        autre, trace_autre, _, _ = self.lancer("double lancement", "--ouvrir-navigateur")
        self.assertNotEqual(autre.wait(timeout=15), 0)
        self.assertFalse(trace_autre.exists(), "Ne pas ouvrir un service qui occupait déjà le port")
        stephanie.send_signal(signal.SIGINT)
        self.assertEqual(stephanie.wait(timeout=5), 0)
        self.attendre(original, "http://127.0.0.1:5005/api/etat", log1)

    def test_port_personnalise_et_ouverture_apres_ecoute(self):
        proc, trace, _, log = self.lancer("port libre", "--port", "0", "--ouvrir-navigateur")
        limite = time.monotonic() + 15
        while not trace.exists() and proc.poll() is None and time.monotonic() < limite:
            time.sleep(0.05)
        log.seek(0)
        self.assertTrue(trace.exists(), log.read())
        url = trace.read_text()
        self.assertNotIn(":0/", url)
        self.assertIn(b"<!DOCTYPE html>", self.attendre(proc, url, log))

    def test_options_incompatibles_refusees_avant_initialisation(self):
        for options in (("--debug",), ("--host", "0.0.0.0")):
            with self.subTest(options=options):
                proc, trace, base, _ = self.lancer(options[-1], "--ouvrir-navigateur", *options)
                self.assertEqual(proc.wait(timeout=15), 2)
                self.assertFalse(trace.exists())
                self.assertFalse((base / "hub.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
