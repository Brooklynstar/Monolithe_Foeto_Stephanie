PLACENTA GÉMELLAIRE
Macroscopie
{% for ligne in placenta_gemellaire.ensemble %}
{{ ligne }}
{% endfor %}
{% for placenta in placenta_gemellaire.placentas %}
Placenta {{ loop.index }}
{% for ligne in placenta.macroscopie %}
{{ ligne }}
{% endfor %}
{% endfor %}
{% if placenta_gemellaire.distance %}
{{ placenta_gemellaire.distance }}
{% endif %}
Microscopie
{% for placenta in placenta_gemellaire.placentas %}
Placenta {{ loop.index }}
{% for ligne in placenta.microscopie %}
{{ ligne }}
{% endfor %}
{% endfor %}
Conclusion
{% for ligne in placenta_gemellaire.conclusion %}
{{ ligne }}
{% endfor %}
