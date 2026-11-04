{% set post_upgrade_types = ["post-upgrade-technisch", "post-upgrade-functioneel"] %}
{% set upgrade_types = ["pre-upgrade"] + post_upgrade_types + ["deprecation"] %}
{% set highlighted_types = ["security-fix"] %}
{# Every other type gets its own top-level section, so new types are never dropped #}
{% set overview_types = definitions|reject("in", upgrade_types + highlighted_types)|list %}
{% macro heading(title, underline) %}
{{ title }}
{{ underline * title|length }}
{% endmacro %}
{% macro entries(category_entries) %}
{% for text, values in category_entries.items() %}
* {% if values %}[{{ values|join(", ") }}]: {% endif %}{{ text }}
{# Nested lists and code blocks must be followed by a blank line #}
{% if "\n\n" in text and not loop.last %}

{% endif %}
{% endfor %}
{% endmacro %}
{% if render_title %}
{{ heading(versiondata.version ~ " (" ~ versiondata.date ~ ")", top_underline) }}
{% endif %}
Voor een volledig overzicht van alle commits, zie :release:`v{{ versiondata.version }}`.

{% for section, categories in sections.items() %}
{% if categories %}
{% if "security-fix" in categories %}
.. admonition:: {{ definitions["security-fix"]["name"] }}
   :class: danger

{{ entries(categories["security-fix"])|indent(3, true) }}
{% endif %}
{% if upgrade_types|select("in", categories)|list %}
{{ heading("Upgrade informatie", "-") }}
{% if "pre-upgrade" in categories %}
{{ heading(definitions["pre-upgrade"]["name"], "~") }}
{{ entries(categories["pre-upgrade"]) }}
{% endif %}
{% if post_upgrade_types|select("in", categories)|list %}
{{ heading("Post-upgrade aandachtspunten", "~") }}
{% for category in post_upgrade_types if category in categories %}
{{ heading(definitions[category]["name"], "^") }}
{{ entries(categories[category]) }}
{% endfor %}
{% endif %}
{% if "deprecation" in categories %}
{{ heading(definitions["deprecation"]["name"], "~") }}
De volgende wijzigingen worden doorgevoerd in de volgende feature release.

{{ entries(categories["deprecation"]) }}
{% endif %}
{% endif %}
{% for category in overview_types if category in categories %}
{{ heading(definitions[category]["name"], "-") }}
{{ entries(categories[category]) }}
{% endfor %}
{% else %}
Geen noemenswaardige wijzigingen.

{% endif %}
{% endfor %}
