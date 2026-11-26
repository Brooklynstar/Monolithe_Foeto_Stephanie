{%- macro titre_placenta(niveau=2) -%}
<h{{ niveau }} style="font:bold 11pt Calibri,Arial,sans-serif;text-decoration:underline;margin:12pt 0 2pt;break-after:avoid;page-break-after:avoid">Placenta</h{{ niveau }}>
{%- endmacro -%}
{%- macro rubrique_placenta(section, niveau=3) -%}
<section style="font:11pt Calibri,Arial,sans-serif;text-align:justify;white-space:normal">
<h{{ niveau }} style="font:inherit;text-decoration:underline;margin:5pt 0 2pt;break-after:avoid;page-break-after:avoid">{{ section.titre }}</h{{ niveau }}>
{% for paragraphe in section.paragraphes %}<p style="margin:0 0 2pt;white-space:pre-line">{{ paragraphe }}</p>
{% endfor %}
</section>
{%- endmacro -%}
