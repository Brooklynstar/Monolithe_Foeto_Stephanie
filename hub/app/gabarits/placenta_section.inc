{% if placenta_html %}
{% from 'placenta_rubriques.inc' import rubrique_placenta, titre_placenta %}
{{ titre_placenta() -}}
{% else %}
PLACENTA
{% endif %}
{% for section in placenta_formulaire.sections %}
{% if placenta_html and section.paragraphes is defined %}
{{ rubrique_placenta(section) -}}
{% elif section.paragraphes is defined %}
{{ section.titre }}
{% for paragraphe in section.paragraphes %}
{{ paragraphe }}
{% endfor %}
{% else %}
{{ section.titre }}
{% for ligne in section.lignes %}
{{ ligne }}
{% endfor %}
{% endif %}
{% endfor %}
