# SPDX-License-Identifier: CC-BY-NC-SA-4.0
"""Probabilité normale et présentation ; aucune table médicale."""
import math
from decimal import Decimal, ROUND_HALF_UP, localcontext
from html import escape


def ecart_exact(valeur, moyenne, sd):
    try:
        v, m, s = float(valeur), float(moyenne), float(sd)
    except (TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(x) for x in (v, m, s)) or s <= 0:
        return None
    z = (v - m) / s
    return z if math.isfinite(z) else None


def percentile(z):
    return 50 * math.erfc(-z / math.sqrt(2)) if isinstance(z, (int, float)) and math.isfinite(z) else None


def decimales(v):
    d = Decimal.from_float(float(v) if v else 0.0)
    with localcontext() as ctx:
        ctx.prec = max(28, d.adjusted() + 4)
        return format(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'f').replace('.', ',')


def pt(p):
    if p is None or not math.isfinite(p):
        return '—'
    return 'P < 0,01' if p < .01 else 'P > 99,99' if p > 99.99 else 'P' + decimales(p)


def zt(z):
    if z is None or not math.isfinite(z):
        return '—'
    return ('+' if z >= 0 else '') + decimales(z).replace('-', '−') + ' DS'


def table(titres, lignes):
    """Colonnes sans valeurs omises ; zéro est une valeur. HTML imprimable."""
    if not lignes:
        return ''
    gardees = [i for i in range(len(titres)) if any(l[i] is not None and str(l[i]).strip() not in ('', '—') for l in lignes)]
    style = 'border:1px solid #999;padding:5px 7px;word-break:normal;overflow-wrap:normal;text-decoration:none;'
    entete = ''.join('<th style="'+style+'text-align:center">'+escape(titres[i]).replace('Z-score','<span style="white-space:nowrap">Z-score</span>')+'</th>' for i in gardees)
    rows = ''.join('<tr>'+''.join('<td style="'+style+'text-align:'+('left' if i == 0 else 'right')+'">'+escape(str(l[i]) if l[i] is not None else '—')+'</td>' for i in gardees)+'</tr>' for l in lignes)
    return '<table style="border-collapse:collapse;font-family:Cambria,\'Times New Roman\',serif;font-size:11pt;width:100%;white-space:normal;break-inside:avoid"><thead>'+entete+'</thead><tbody>'+rows+'</tbody></table>'
