==================
Open Inwoner
==================


:Version: 2.4.2
:Demo: https://openinwoner.nl
:Source: https://github.com/maykinmedia/open-inwoner
:Documentation: https://docs.openinwoner.nl
:PythonVersion: 3.13

|build-status| |docker| |ruff| |python-versions| |storybook|

Platform voor gemeenten en overheden om producten inzichtelijker en toegankelijker te maken voor inwoners.

Ontwikkeld door `Maykin Media B.V.`_ voor Dimpact en de `Open Inwoner`_ gemeenten:
Deventer, Enschede, Groningen, Leeuwarden, Hoorn, Zwolle.


Introductie
============

Het Open Inwoner Platform is ontwikkeld voor en door gemeenten om producten en diensten aan te bieden aan hun inwoners, gecombineerd met een "Mijn" omgeving.

Informatie over de producten kan eenvoudig beheerd worden middels een handige WYSIWYG editor. Gebruikers van het platform kunnen door de beschikbare producten zoeken, veelgestelde vragen bekijken en tevens eenvoudige vragenlijsten invullen om zo de voor hun relevante informatie zo laagdrempelig mogelijk te vinden.

Gebruikers kunnen tevens berichten en documenten uitwisselen, dit vindt plaats door middel van samenwerkingsplannen en desgewenst zonder of met de gemeente.

Zie voor meer informatie de demo-omgeving op https://openinwoner.nl waarop de verschillende onderdelen van het Open Inwoner Platform worden toegelicht.

Open Inwoner is ontwikkeld in lijn met de `Common Ground`_ principes en bevat integraties met Common Ground componenten zoals Open Zaak en Haal Centraal.


Introduction (English)
======================

Open Inwoner is a Dutch citizen-facing government services platform ("MijnGemeente" / "My Municipality" portal) that enables municipalities to provide personalized digital services to their citizens.

Key capabilities:

* Present government products and services in an accessible, user-friendly manner
* Provide a personalized "Mijn" (My) environment for citizens to manage documents and messages
* Enable collaboration between citizens and government through shared plans
* Integrate with Common Ground (Dutch government standardization) components


Technology Stack
================

Backend
-------

==================== ===================================================
Component            Technology
==================== ===================================================
Framework            Django 5.2 (Python 3.13)
Database             PostgreSQL with PostGIS extension (geographic data)
Caching              Redis with django-redis
Task Queue           Celery with Redis backend
Search               Elasticsearch with django-elasticsearch-dsl
CMS                  Django CMS 3.11
API                  Django REST Framework with OpenAPI documentation
==================== ===================================================

Frontend
--------

==================== ===================================================
Component            Technology
==================== ===================================================
JavaScript Framework Preact (web components) with TypeScript
Build Tool           Vite
Component Library    Storybook
Dynamic UI           HTMX for lightweight dynamic updates
Design System        NLDS design system components
==================== ===================================================

Infrastructure
--------------

* **Logging**: Structlog with JSON output in production
* **Error Tracking**: Sentry SDK integration
* **APM**: Elastic APM support
* **Observability**: OpenTelemetry instrumentation for distributed tracing
* **Health Checks**: Django health check framework

Integrations
============

Authentication
--------------

* **DigiD** - Dutch citizen authentication
* **eHerkenning** - Dutch business authentication
* **OpenID Connect** - Standard OIDC provider support
* **2FA/WebAuthn** - Two-factor authentication for admin accounts

Common Ground / ZGW
-------------------

* **Open Zaak** - Case management (Zaakgericht Werken APIs)
* **Open Klant** - Customer/citizen data management (Klantinteractie APIs)
* **Haal Centraal BRP** - Citizen data retrieval from the BRP (Basisregistratie Personen)

Other Services
--------------

* **KvK (Kamer van Koophandel)** - Dutch Chamber of Commerce for business data
* **Qmatic** - External appointment management system
* **Laposta** - Newsletter and mailing list integration

Documentation
=============

See ``INSTALL.rst`` for installation instructions, available settings and
commands.

Full documentation is available at https://docs.openinwoner.nl


License
=======

Copyright © Maykin Media, 2026

Licensed under the EUPL_.


References
==========

* `Demo website <https://openinwoner.nl>`_
* `Issues <https://github.com/maykinmedia/open-inwoner/issues>`_
* `Documentation <https://docs.openinwoner.nl>`_
* `Code <https://github.com/maykinmedia/open-inwoner>`_
* `Docker image <https://hub.docker.com/r/maykinmedia/open-inwoner>`_

.. |build-status| image:: https://github.com/maykinmedia/open-inwoner/actions/workflows/ci.yml/badge.svg?branch=develop
    :alt: Build status
    :target: https://github.com/maykinmedia/open-inwoner/actions/workflows/ci.yml

.. |ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :alt: Ruff
    :target: https://github.com/astral-sh/ruff

.. |docker| image:: https://img.shields.io/docker/v/maykinmedia/open-inwoner
    :alt: Docker image
    :target: https://hub.docker.com/r/maykinmedia/open-inwoner

.. |python-versions| image:: https://img.shields.io/badge/python-3.13-blue.svg
    :alt: Supported Python version

.. |storybook| image:: https://img.shields.io/badge/storybook-live-FF4785.svg?logo=storybook
    :alt: Open Inwoner Storybook
    :target: https://maykinmedia.github.io/open-inwoner


.. _Common Ground: https://commonground.nl/
.. _Maykin Media B.V.: https://www.maykinmedia.nl
.. _Open Inwoner: https://openinwoner.nl
.. _i4Sociaal: https://www.dimpact.nl/i4sociaal
.. _EUPL: LICENSE.md
