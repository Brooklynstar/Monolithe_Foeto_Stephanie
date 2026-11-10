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

    def test_port_5006_par_defaut_et_port_occupe(self):
        with socket.socket() as sonde:
            try:
                sonde.bind(("127.0.0.1", 5006))
            except OSError:
                self.skipTest("port 5006 occupé par un service extérieur")
        proc, trace, base, log = self.lancer("Stéphanie avec espaces", "--ouvrir-navigateur")
        self.attendre(proc, "http://127.0.0.1:5006/", log)
        self.assertEqual(trace.read_text(), "http://127.0.0.1:5006/")
        etat = json.loads(self.attendre(proc, "http://127.0.0.1:5006/api/etat", log))
        self.assertEqual(etat["racine"], str(base))
        autre, trace_autre, _, _ = self.lancer("double lancement", "--ouvrir-navigateur")
        self.assertNotEqual(autre.wait(timeout=15), 0)
        self.assertFalse(trace_autre.exists())
        self.attendre(proc, "http://127.0.0.1:5006/api/etat", log)

    @unittest.skipUnless(os.name == "posix", "Bash nécessaire")
    def test_lanceur_command_chemin_avec_espaces_et_erreur(self):
        app = self.racine / "Stéphanie avec espaces" / "hub" / "app"
        app.mkdir(parents=True)
        shutil.copy(APP / "serveur.command", app)
        shutil.copy(APP.parents[1] / "serveur.command", app.parents[1])
        shutil.copy(APP / "requirements.txt", app)
        venv = app / ".venv"
        (venv / "bin").mkdir(parents=True)
        shutil.copy(app / "requirements.txt", venv / "requirements-installes.txt")
        python = venv / "bin" / "python"
        python.write_text('#!/bin/bash\nif [ "$1" = "-c" ]; then exit 0; fi\nprintf "%s\\n" "$@" > "' + str(app / "arguments.txt") + '"\nexit "${TEST_LANCEMENT_CODE:-0}"\n')
        python.chmod(0o755)
        commande = ["bash", str(app.parents[1] / "serveur.command")]
        r = subprocess.run(commande, cwd="/tmp", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((app / "arguments.txt").read_text().splitlines(),
                         [str(app / "serveur.py"), "--base", str(app / ".."), "--ouvrir-navigateur"])
        # Le fichier local peut désigner la même base habituelle, sans copie.
        existante = self.racine / "Base habituelle avec espaces"
        existante.mkdir()
        (existante / "hub.sqlite").write_bytes(b"temoin fictif non modifie")
        config = app.parents[1] / "base_locale.txt"
        config.write_text(str(existante) + "\n")
        r = subprocess.run(commande, cwd="/tmp", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(str(existante), (app / "arguments.txt").read_text().splitlines())
        self.assertEqual((existante / "hub.sqlite").read_bytes(), b"temoin fictif non modifie")
        config.write_text(str(existante / "introuvable") + "\n")
        r = subprocess.run(commande, cwd="/tmp", capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertFalse((existante / "introuvable").exists())
        config.unlink()
        r = subprocess.run(commande, cwd="/tmp", capture_output=True, text=True,
                           env={**os.environ, "TEST_LANCEMENT_CODE": "9"})
        self.assertEqual(r.returncode, 9)
        self.assertIn("Lancement interrompu", r.stdout)

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
