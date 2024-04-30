{% block link %}{{ link }}{% endblock %}

{% block title %}{{ title }}{% endblock %}

Settings Overview
=================

Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    {% spaceless %}
    {{ enable_settings }}
    {% endspaceless %}

Required:
"""""""""

::

    {% spaceless %}
    {% for setting in required_settings %}{{ setting }}
    {% endfor %}
    {% endspaceless %}

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
