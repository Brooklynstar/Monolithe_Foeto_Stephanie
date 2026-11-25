PLACENTA
{% for section in placenta_formulaire.sections %}
{{ section.titre }}
{% for ligne in section.lignes %}
{{ ligne }}
{% endfor %}
{% endfor %}
