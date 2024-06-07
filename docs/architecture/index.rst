=========================================
Architecture and Common Ground principles
=========================================

OIP is a 'My Municipality' webapplication component that targets the "Interactie" en "Procesinrichting" layers of the `Common Ground`_ 5-layer architecture.

Common Ground principles
========================

 * Component-based: OIP can be used as a stand-alone solution, however as a platform OIP becomes much more useful when used in conjunction with integrations for authentication (DigiD, eHerkenning, OIDC), forms (Open Formulieren) and cases (Open Zaak / ZGW APIs)
 * Open & Open Source: The codebase is publicly available on `Github`_ under the EUPL and releases are pushed to the `Docker Hub`_
 * Secure: OIP receives yearly pentests and changes are reviewed for security. OIP has >90% test coverage which cover both features and security
 * Single Datasource: OIP obtains data from registration-components like Open Zaak and Open Klant
 * Data Ownership: Citizens have direct access to their data and can delete their profile at any time
 * Standards & Modern IT: OIP is built upon modern REST APIs and standards like the VNG ZGW APIs in order to allow for easy integration and data portability
 * Community & Agile: The development of OIP is driven by 6 municipalities together with Dimpact in a per-sprint basis with monthly releases

Architecture
============

OIP is a Python/Django webapplication which offers a large degree of flexibility to the municipality using it. Customization is facilitated by an extensive range of configuration settings in the admin, combined with Django CMS for structuring the pages and page structure of the instance.

The Django code-base is structured into a range of built-in Django apps, one for each integration (`haalcentraal`, `openzaak`, `openklant` etc).

For making use of these integrations in a pluggable fashion, OIP uses Django CMS apphooks which can be found in the `cms` app:

 * `products` publishes the PDC / Category and Product details to anonymous and logged-in users (eg. Productenpagina's)
 * `cases` exposes the Open Zaak case details to logged-in users (eg. Mijn aanvragen)
 * `collaborate` exposes the cooperative planning module to logged-in users (eg. Samenwerken)
 * `inbox` exposes the internal messaging app to logged-in users (eg. Mijn Berichten)
 * `profile` exposes the profile to logged-in users (eg. Mijn Profiel)
 * `benefits` exposes functionality to download benefit specifications via SSD to logged-in users (eg. Mijn Uitkeringen)

Each of these `cms` apps can be individually enabled or disabled by (de)activating a Django CMS apphook for that app via the CMS admin interface. Enabling the apphook enables the feature on the CMS page on which it is activated. Generic OIP Django apps like `accounts` are always active and provide overall authentication/authorization and user management features.

 * For the frontend OIP makes use of SCSS and Javascript, with HTMX/django-htmx integration for specific use-cases which require dynamic content
 * For the database OIP makes use of PostgreSQL
 * For caching and task queues OIP makes use of Redis
 * For background tasks OIP uses Celery combined with Celery Beat
 * For search OIP integrates with ElasticSearch

With OIP we make use of a number of shared Maykin-built Django apps like django-digid-eherkenning, zgw-consumers, notifications-api-common, maykin-2fa, django-admin-index, django-open-forms-client, django-log-outgoing-requests, django-setup-configuration and mozilla-django-oidc-db.


Datamodels
==========

Generated based on OIP v1.17

Accounts app
.. graphviz:: accounts.dot

Configuration app	      
.. graphviz:: configurations.dot

Haal Centraal app
.. graphviz:: haalcentraal.dot

KVK app
.. graphviz:: kvk.dot

Open Klant app
.. graphviz:: openklant.dot

Open Zaak app
.. graphviz:: openzaak.dot	    

PDC app
.. graphviz:: pdc.dot

Plans app
.. graphviz:: plans.dot
	      
.. _Common Ground: https://commonground.nl
.. _Github: https://github.com/maykinmedia/open-inwoner
.. _Docker Hub: https://hub.docker.com/repository/docker/maykinmedia/open-inwoner
