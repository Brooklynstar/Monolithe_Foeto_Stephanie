#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Base exclusivement fictive ; aucun paramètre ne cible la base clinique du Hub."""
import argparse
import json
from pathlib import Path
import sys
import shutil
import webbrowser

DEPOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(DEPOT / 'hub/app'))
import biometrie
import cr
import ingest
import serveur

NUMERO = 'DEMO_SLO_001'
SOURCES = DEPOT / 'hub/demonstrations' / NUMERO
BASE = DEPOT / '.demo-slo' / 'base'
MARQUEUR = '.demonstration-slo.json'
SIGNATURE = {'usage': 'demonstration-exclusivement-fictive', 'dossier': NUMERO, 'version': 1}


def verifier_base(base):
    """Refuser AVANT toute migration/ingestion un répertoire non réservé au test."""
    base = Path(base).resolve()
    if base == (DEPOT / 'hub').resolve():
        raise ValueError('La base clinique hub est interdite.')
    marqueur = base / MARQUEUR
    if base.exists() and any(base.iterdir()):
        if not marqueur.is_file() or json.loads(marqueur.read_text()) != SIGNATURE:
            raise ValueError('Dossier non réservé à la démonstration : chargement refusé.')
        if (base / 'hub.sqlite').exists():
            import sqlite3
            with sqlite3.connect(f'file:{base / "hub.sqlite"}?mode=ro', uri=True) as cx:
                numeros = {r[0] for r in cx.execute('SELECT numero FROM dossiers')}
            if numeros - {NUMERO}:
                raise ValueError('Autre dossier détecté : chargement de données fictives refusé.')
    return base


def documents():
    docs = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(SOURCES.glob('*.json'))]
    refs = biometrie.References()
    for d in docs:
        if d['module'] == 'biometrie_clinique':
            # Le moteur existant produit tous les résultats. Sources sans Z ni P saisis.
            resultats = biometrie.calculer(refs, d['terme']['sa'], None, {}, d['mesures'])
            for champ, prefixe in [('ecarts', 'z_'), ('ecarts_non_arrondis', 'z_brut_'), ('percentiles', 'percentile_')]:
                d[champ] = {k: {src: resultats.get('bio_' + k, {}).get(prefixe + src.lower())
                               for src in ('GC', 'MA', 'MB')}
                            for k, v in d['mesures'].items() if v is not None}
            mesures = refs.biometrie_clinique['mesures']
            d['libelles'] = {k: v['libelle'] for k, v in mesures.items()}
            d['unites'] = {k: v['unite'] for k, v in mesures.items()}
    return sorted(docs, key=lambda d: d['module'] != 'administratif')


def preparer(base=BASE, reinitialiser=False):
    base = verifier_base(base)
    if reinitialiser and base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    (base / MARQUEUR).write_text(json.dumps(SIGNATURE), encoding='utf-8')
    ingest.arborescence(base)
    cx, _ = ingest.ouvrir(base / 'hub.sqlite')
    try:
        ingest.migrer(cx, DEPOT / 'hub/app/migrations', bavard=False)
        modifie = False
        for d in documents():
            brut = (json.dumps(d, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
            courant = cx.execute('SELECT sha256 FROM saisies WHERE dossier=? AND module=? AND courant=1', (NUMERO, d['module'])).fetchone()
            modifie |= courant is None or courant[0] != ingest.sha256(brut)
            _, _, sid = ingest.ingerer(cx, base, brut, d['module'] + '.json', provenance='poste')
            ingest.rendre_courante(cx, sid)
        cx.execute('UPDATE dossiers SET remarques=?, assigne_a=? WHERE numero=?',
                   ('DÉMONSTRATION — Syndrome de Smith-Lemli-Opitz — CAS ENTIÈREMENT FICTIF', 'Codex', NUMERO))
        refs = biometrie.References(base)
        for gabarit in ('complet', 'synthese'):
            # La relance ne multiplie ni les saisies ni les comptes rendus.
            if modifie or not cx.execute('SELECT 1 FROM comptes_rendus WHERE dossier=? AND gabarit=?',
                              (NUMERO, gabarit)).fetchone():
                cr.rendre(cx, NUMERO, gabarit, refs, ingest.ORDRE_MODULES, operateur='Codex')
        cx.commit()
        ingest.ecrire_index(cx, base)
    finally:
        cx.close()
    return base


def application(base):
    from flask import jsonify
    app = serveur.creer_app(base, DEPOT)

    @app.get('/demonstration/export.json')
    def exporter():
        cx, _ = ingest.ouvrir(base / 'hub.sqlite')
        try:
            saisies = [json.loads(r[0]) for r in cx.execute(
                'SELECT donnees_json FROM saisies WHERE dossier=? AND courant=1 ORDER BY module', (NUMERO,))]
            ctx = cr.contexte(cx, NUMERO, biometrie.References(base), ingest.ORDRE_MODULES)
            return jsonify({'fictif': True, 'dossier': NUMERO, 'saisies': saisies,
                            'biometries_calculees': ctx['biometrie']['lignes']})
        finally:
            cx.close()
    @app.after_request
    def signaler_demonstration(reponse):
        if reponse.mimetype == 'text/html' and reponse.status_code == 200 and __import__('flask').request.path == '/':
            bandeau = ('<aside style="padding:12px;background:#fff1c2;color:#352600;font:16px system-ui" role="note">'
                       '<strong>DÉMONSTRATION — Syndrome de Smith-Lemli-Opitz</strong> — '
                       'CAS ENTIÈREMENT FICTIF. Base locale de test ; ne pas y déposer de dossier réel. '
                       '<a href="/demonstration/export.json" download="DEMO_SLO_001.json">Exporter le dossier JSON</a></aside>')
            reponse.direct_passthrough = False
            texte = reponse.get_data(as_text=True)
            reponse.close()
            texte = texte.replace('<body>', '<body>' + bandeau, 1)
            # Valeur locale de cette page, sans modifier les préférences du Hub clinique.
            texte = texte.replace('</body>', '<script>document.getElementById("operateur").value="Codex";</script></body>')
            reponse.set_data(texte)
        return reponse
    return app


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preparer', action='store_true', help='charger sans démarrer le navigateur')
    ap.add_argument('--port', type=int, default=5005)
    ap.add_argument('--reinitialiser', action='store_true', help='réinstaller uniquement la base fictive marquée ; efface ses essais')
    args = ap.parse_args()
    base = preparer(reinitialiser=args.reinitialiser)
    print(f'CAS FICTIF UNIQUEMENT — base isolée : {base}')
    if args.preparer:
        return
    from werkzeug.serving import make_server
    # Réserver avant ouverture : pas de navigateur ouvert sur une base clinique existante.
    with make_server('127.0.0.1', args.port, application(base)) as http:
        url = f'http://127.0.0.1:{http.server_port}/'
        print(f'{url}\nChoisir {NUMERO} ; Ctrl+C pour arrêter.')
        if not webbrowser.open(url):
            print('Ouvrir cette adresse dans le navigateur.')
        try:
            http.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
