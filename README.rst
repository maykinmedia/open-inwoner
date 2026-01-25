==================
Open Inwoner
==================


:Version: 2.1.0-dev
:Demo: https://openinwoner.nl
:Source: https://github.com/maykinmedia/open-inwoner
:Documentation: https://docs.openinwoner.nl
:PythonVersion: 3.12

|build-status| |docker| |black| |python-versions|

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
Framework            Django 4.2 (Python 3.12)
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
JavaScript Framework React 18 with TypeScript
Build Tool           Vite
Component Library    Storybook
Dynamic UI           HTMX for lightweight dynamic updates
Design System        Utrecht design system components
==================== ===================================================

Infrastructure
--------------

* **Logging**: Structlog with JSON output in production
* **Error Tracking**: Sentry SDK integration
* **APM**: Elastic APM support
* **Observability**: OpenTelemetry instrumentation for distributed tracing
* **Health Checks**: Django health check framework


Project Structure
=================

::

    src/open_inwoner/
    ├── accounts/       # User authentication & profiles
    ├── pdc/            # Product Data Catalog (main service listings)
    ├── plans/          # Collaboration plans between citizens and government
    ├── cms/            # Content management (Django CMS)
    ├── api/            # REST API endpoints
    ├── search/         # Elasticsearch-powered search
    ├── questionnaire/  # Form/questionnaire builder
    ├── openzaak/       # Open Zaak API integration (case management)
    ├── openklant/      # OpenKlant API integration (customer data)
    ├── haalcentraal/   # Haal Centraal API integration (citizen data)
    ├── kvk/            # Dutch Chamber of Commerce integration
    ├── laposta/        # Newsletter integration
    ├── qmatic/         # External appointment management integration
    ├── mail/           # Email/messaging functionality
    ├── userfeed/       # User activity feed
    ├── components/     # Reusable component library
    ├── htmx/           # HTMX integration for dynamic updates
    ├── react/          # React frontend components
    ├── static/         # CSS, JS, assets
    ├── templates/      # Django HTML templates
    └── utils/          # Shared utilities


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

* **Open Zaak** - Case management (Zaakgericht Werken)
* **OpenKlant** - Customer/citizen data management
* **Haal Centraal BRP** - Citizen data retrieval from the BRP (Basisregistratie Personen)

Other Services
--------------

* **KvK (Kamer van Koophandel)** - Dutch Chamber of Commerce for business data
* **Qmatic** - External appointment management system
* **LaPoSta** - Newsletter and mailing list integration


Architecture Highlights
=======================

* **Multi-frontend approach**: Combines Django templates for server-rendered pages, React components for interactive UI, and HTMX for lightweight dynamic updates
* **API-first design**: REST API with Django REST Framework and OpenAPI/Swagger documentation
* **Modular architecture**: Each feature area is a self-contained Django app with models, views, serializers, and templates
* **Security-by-default**: CSP headers, 2FA/WebAuthn for admin, government-grade authentication integrations
* **Geospatial capabilities**: PostGIS support with Leaflet mapping for location-based services
* **12-factor app**: Environment-driven configuration for easy deployment


Documentation
=============

See ``INSTALL.rst`` for installation instructions, available settings and
commands.

Full documentation is available at https://docs.openinwoner.nl


License
=======

Copyright © Maykin Media, 2024

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

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :alt: Code style
    :target: https://github.com/psf/black

.. |docker| image:: https://img.shields.io/docker/v/maykinmedia/open-inwoner
    :alt: Docker image
    :target: https://hub.docker.com/r/maykinmedia/open-inwoner

.. |python-versions| image:: https://img.shields.io/badge/python-3.12-blue.svg
    :alt: Supported Python version


.. _Common Ground: https://commonground.nl/
.. _Maykin Media B.V.: https://www.maykinmedia.nl
.. _Open Inwoner: https://openinwoner.nl
.. _i4Sociaal: https://www.dimpact.nl/i4sociaal
.. _EUPL: LICENSE.md
