# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Import explicite d'un dossier complet par la chaîne d'ingestion habituelle."""
import json
import re
from html import escape
from html.parser import HTMLParser

TYPE = 'monolithe_dossier'


class _HTMLRapport(HTMLParser):
    tags = set('div section article p br h1 h2 h3 h4 table thead tbody tfoot tr td th strong b em i u span ul ol li pre hr sub sup'.split())
    styles = set('border border-collapse border-bottom padding margin font font-family font-size font-weight font-style text-align text-decoration white-space word-break overflow-wrap width height max-width min-width background background-color color table-layout break-inside page-break-inside break-after page-break-after display vertical-align line-height letter-spacing'.split())

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.bloque = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'iframe', 'object', 'svg', 'math', 'template'):
            self.bloque += 1
            return
        if self.bloque or tag not in self.tags:
            return
        propres = []
        for k, v in attrs:
            if v is None:
                continue
            if k == 'style':
                regles = []
                for regle in v.split(';'):
                    propriete, _, valeur = regle.partition(':')
                    if propriete.strip().lower() in self.styles and not re.search(r'url|expression|[\\<>@]', valeur, re.I):
                        regles.append(propriete.strip().lower() + ':' + valeur)
                propres.append(('style', ';'.join(regles)))
            elif k in ('colspan', 'rowspan') and v.isdigit() and 0 < int(v) <= 100:
                propres.append((k, v))
            elif k == 'data-mesure':
                propres.append((k, v))
        self.out.append('<' + tag + ''.join(f' {k}="{escape(v, quote=True)}"' for k, v in propres) + '>')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'iframe', 'object', 'svg', 'math', 'template'):
            self.bloque = max(0, self.bloque - 1)
        elif not self.bloque and tag in self.tags:
            self.out.append('</' + tag + '>')

    def handle_data(self, data):
        if not self.bloque:
            self.out.append(escape(data))


def rapport_sur(texte, fmt):
    if not isinstance(texte, str) or not texte.strip() or len(texte) > 2_000_000:
        raise ValueError('Compte rendu vide, trop long ou invalide.')
    if fmt not in ('html', 'texte'):
        raise ValueError('Format de compte rendu inconnu.')
    if fmt == 'texte':
        return texte
    parser = _HTMLRapport()
    parser.feed(texte)
    parser.close()
    return ''.join(parser.out)


def importer(cx, racine, brut, nom, dry=False):
    import ingest
    try:
        paquet = json.loads(brut.decode('utf-8-sig'))
    except (ValueError, UnicodeError):
        return None  # L'import standard produit son diagnostic habituel.
    if not isinstance(paquet, dict) or paquet.get('type') != TYPE:
        return None
    numero = paquet.get('dossier')
    docs, rapports = paquet.get('saisies'), paquet.get('comptes_rendus', [])
    if paquet.get('version') != 1 or not isinstance(numero, str) or not ingest.DOSSIER_RE.fullmatch(numero):
        raise ingest.Refus('Enveloppe de dossier portable invalide.')
    if not isinstance(docs, list) or not docs or len(docs) > 100 or not isinstance(rapports, list) or len(rapports) > 100:
        raise ingest.Refus('Liste de saisies ou de comptes rendus invalide.')
    enveloppes, modules, crs = [], set(), []
    for doc in docs:
        if not isinstance(doc, dict) or doc.get('dossier') != numero:
            raise ingest.Refus('Toutes les saisies doivent appartenir au même dossier.')
        b = (json.dumps(doc, ensure_ascii=False, sort_keys=True) + '\n').encode()
        d = ingest.lire_enveloppe(b, f"{numero}_{doc.get('module')}.json")
        if d['module'] in modules:
            raise ingest.Refus('Deux saisies pour le même module dans le dossier portable.')
        modules.add(d['module'])
        enveloppes.append((d, b))
    for r in rapports:
        try:
            if not isinstance(r, dict):
                raise ValueError('Compte rendu invalide.')
            g = r.get('gabarit')
            if not isinstance(g, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,40}', g):
                raise ValueError('Gabarit de compte rendu invalide.')
            fmt = r.get('format', 'texte')
            crs.append((g, str(r.get('gabarit_version') or '')[:40],
                        rapport_sur(r.get('texte'), fmt), str(r.get('operateur') or '')[:100], fmt))
        except ValueError as e:
            raise ingest.Refus(str(e)) from e
    if cx.execute('SELECT 1 FROM dossiers WHERE numero=?', (numero,)).fetchone():
        return 'doublon', f'{numero} existe déjà : aucune donnée ni correction remplacée', None
    if dry:
        return 'info', f'{numero} : {len(docs)} saisies et {len(crs)} comptes rendus', None
    # Aucun démarrage ne passe ici : uniquement le dépôt explicite d'un JSON.
    avant = set((racine / 'archive' / numero).rglob('*.json'))
    cx.execute('SAVEPOINT dossier_portable')
    try:
        for doc, b in sorted(enveloppes, key=lambda x: x[0]['module'] != 'administratif'):
            ingest.ingerer(cx, racine, b, f"{numero}_{doc['module']}.json")
        for g, version, texte, operateur, fmt in crs:
            cx.execute('INSERT INTO comptes_rendus(dossier,gabarit,gabarit_version,texte,operateur,format) VALUES (?,?,?,?,?,?)',
                       (numero, g, version, texte, operateur, fmt))
        titre = str(paquet.get('nom') or '')[:500]
        cx.execute('UPDATE dossiers SET remarques=?, assigne_a=? WHERE numero=?',
                   (titre or None, str(paquet.get('operateur') or '')[:100] or None, numero))
        cible = racine / 'archive' / numero / ('dossier_' + ingest.sha256(brut)[:16] + '.json')
        cible.write_bytes(brut)
        cx.execute('RELEASE SAVEPOINT dossier_portable')
    except Exception:
        cx.execute('ROLLBACK TO SAVEPOINT dossier_portable')
        cx.execute('RELEASE SAVEPOINT dossier_portable')
        for chemin in set((racine / 'archive' / numero).rglob('*.json')) - avant:
            chemin.unlink()
        raise
    return 'info', f'{numero} : {len(docs)} saisies et {len(crs)} comptes rendus importés', None
