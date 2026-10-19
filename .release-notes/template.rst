{% set upgrade_types = ["breaking", "actiepunt", "aandachtspunt"] %}
{% set highlight_type = "belangrijk" %}
{% set security_types = ["security", "security-improvement"] %}
{% set placed_types = upgrade_types + security_types + ["deprecation", highlight_type] %}
{# Every other type ends up under "Alle wijzigingen", so new types are never dropped #}
{% set overview_types = definitions|reject("in", placed_types)|list %}
{% macro entries(category_entries) %}
{% for text, values in category_entries.items() %}
* {{ text }}

{% endfor %}
{% endmacro %}
{% macro admonition(title, kind, types, categories) %}
{% if types|select("in", categories)|list %}
.. admonition:: {{ title }}
   :class: {{ kind }}

{% for category in definitions if category in types and category in categories %}
{% if types|length > 1 %}
   **{{ definitions[category]['name'] }}**

{% endif %}
{% for text, values in categories[category].items() %}
   * {{ text|indent(3) }}

{% endfor %}
{% endfor %}
{% endif %}
{% endmacro %}
{% macro linked_entries(category_entries) %}
{% for text, values in category_entries.items() %}
* {% if values %}[{{ values|join(", ") }}] {% endif %}{{ text }}

{% endfor %}
{% endmacro %}
{% macro group(title, types, categories) %}
{% if types|select("in", categories)|list %}
{{ title }}
{{ "_" * title|length }}

{% for category in definitions if category in types and category in categories %}
**{{ definitions[category]['name'] }}**

{{ linked_entries(categories[category]) }}
{% endfor %}
{% endif %}
{% endmacro %}
{% if render_title %}
{% if versiondata.name %}
{{ versiondata.name }} {{ versiondata.version }} ({{ versiondata.date }})
{{ top_underline * ((versiondata.name + versiondata.version + versiondata.date)|length + 4)}}
{% else %}
{{ versiondata.version }} ({{ versiondata.date }})
{{ top_underline * ((versiondata.version + versiondata.date)|length + 3)}}
{% endif %}

{% endif %}
{% for section, categories in sections.items() %}
{% if categories %}
{# Only security fixes that need immediate action make the block red #}
{{ admonition("Beveiliging", "danger" if "security" in categories else "note", security_types, categories) }}
{# Upgrade instructions with breaking changes get a warning instead of an info style #}
{{ admonition("Upgrade-instructies", "warning" if "breaking" in categories else "note", upgrade_types, categories) }}
{{ admonition(definitions["deprecation"]["name"], "note", ["deprecation"], categories) }}
{% if highlight_type in categories %}
{{ definitions[highlight_type]["name"] }}
{{ "_" * definitions[highlight_type]["name"]|length }}

{{ entries(categories[highlight_type]) }}
{% endif %}
{{ group("Alle wijzigingen", overview_types, categories) }}
{% else %}
Geen noemenswaardige wijzigingen.


{% endif %}
{% endfor %}
