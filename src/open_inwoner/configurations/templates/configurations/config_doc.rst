{% block link %}{{ link }}{% endblock %}

{% block title %}{{ title }}{% endblock %}

Settings Overview
=================

{% if enable_setting %}
Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    {% spaceless %}
    {{ enable_setting }}
    {% endspaceless %}
{% endif %}

{% if required_settings %}
Required:
"""""""""

::

    {% spaceless %}
    {% for setting in required_settings %}{{ setting }}
    {% endfor %}
    {% endspaceless %}
{% endif %}

All settings:
"""""""""""""

::

    {% spaceless %}
    {% for setting in all_settings %}{{ setting }}
    {% endfor %}
    {% endspaceless %}

Detailed Information
====================

::

    {% spaceless %}
    {% for detail in detailed_info %}
    {% for part in detail %}{{ part|safe }}
    {% endfor %}{% endfor %}
    {% endspaceless %}
