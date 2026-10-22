.. _installation_development:

===========
Development
===========

This installs every dependency (Postgres, Elasticsearch, Node, ...) directly
on your machine, with no Docker at all. For most development work, running
:ref:`Docker-Compose <installation_docker_compose_host_mode>` for the
satellites/backing services and Open Inwoner itself on the host is
considerably less setup -- use this fully native path only if Docker isn't
an option for you.

Prerequisites
-------------

You need the following libraries and/or programs:

* `Python`_ 3.13 or above
* Python `Virtualenv`_ and `Pip`_
* `PostgreSQL`_ 10 or above with PostGIS extension
* `Node.js`_ 24.15
* `npm`_
* `Elastic Search`_ 7.9.2 or above

You will also need the `Libxml2`_ and `GDAL`_ development libraries.
For Linux (Debian) they are following:

* libxml2-dev
* libxmlsec1-dev
* libxmlsec1-openssl
* libgdal-dev
* gdal-bin

.. _Python: https://www.python.org/
.. _Virtualenv: https://virtualenv.pypa.io/en/stable/
.. _Pip: https://packaging.python.org/tutorials/installing-packages/#ensure-pip-setuptools-and-wheel-are-up-to-date
.. _PostgreSQL: https://www.postgresql.org
.. _Node.js: http://nodejs.org/
.. _npm: https://www.npmjs.com/
.. _Elastic Search: https://www.elastic.co/
.. _Libxml2: https://gitlab.gnome.org/GNOME/libxml2/-/wikis/home
.. _GDAL: https://gdal.org/


Getting started
---------------

Developers can follow the following steps to set up the project on their local
development machine.

1. Navigate to the location where you want to place your project.

2. Get the code:

   .. code-block:: bash

       git clone git@github.com:maykinmedia/open-inwoner.git
       cd open-inwoner
       # initialize submodules
       git submodule update --init --recursive

This will include the `Open-Inwoner-Design-Tokens`_ subdirectory. When all is built and run this is where the OIP design tokens CSS will be generated. When this repository gets updated, it needs to be pulled again.

.. _Open-Inwoner-Design-Tokens: https://github.com/maykinmedia/open-inwoner-design-tokens

3. Install all required (backend) libraries.
   **Tip:** You can use the ``bootstrap.py`` script to install the requirements
   and set the proper settings in ``manage.py``. Or, perform the steps
   manually:

   .. code-block:: bash

       virtualenv env
       source env/bin/activate
       pip install -r requirements/dev.txt

4. Run third-party install commands:

   - Install the required browsers for `Playwright`_ end-to-end testing.

   .. code-block:: bash

       playwright install

.. _Playwright: https://playwright.dev/python/

5. Install and build the frontend libraries:

   .. code-block:: bash

       npm install
       npm run build

6. Create the statics and database:

   .. code-block:: bash

       python src/manage.py collectstatic --link
       python src/manage.py migrate

7. Create a superuser to access the management interface:

   .. code-block:: bash

       python src/manage.py createsuperuser

8. You can now run your installation and point your browser to the address
   given by this command:

   .. code-block:: bash

       python src/manage.py runserver

9. Create a .env file with database settings. See dotenv.example for an example.

   .. code-block:: bash

       cp dotenv.example .env

**Note:** If you are making local, machine specific, changes, add them to
``src/open_inwoner/conf/local.py``. You can base this file on the
example file included in the same directory.

**Note:** While working on the frontend, run ``npm run watch`` to start the
Vite dev server, which hot reloads your `Sass`_ and JavaScript changes in the
browser. See `Frontend assets (Vite)`_ below.

.. _Sass: https://sass-lang.com/


Frontend assets (Vite)
----------------------

The frontend is built with `Vite`_, and Django finds the build output through
`django-vite`_.

How it works
~~~~~~~~~~~~

``npm run build`` writes the bundles to ``src/open_inwoner/static/bundles/``.
Every file name contains a content hash (e.g. ``index.3f9a1c.js``), and Vite
also writes a ``manifest.json`` that maps each entry point to its hashed
output. Templates don't hardcode bundle names: they reference the source
entries, and django-vite looks up the hashed files in the manifest:

.. code-block:: django

    {% vite_asset_url 'src/open_inwoner/scss/screen.scss' %}
    {% vite_asset 'src/open_inwoner/js/index.js' nonce=request.csp_nonce %}

django-vite reads the manifest from the build directory, not from
``STATIC_ROOT``, so it works without running ``collectstatic``. It's configured
with the ``DJANGO_VITE`` setting in ``src/open_inwoner/conf/base.py``.

Without a build (and without the dev server running, see below) the manifest
doesn't exist and the pages can't load their CSS and JavaScript, so run
``npm run build`` at least once.

In production, ``collectstatic`` uses
``open_inwoner.utils.files.ViteManifestStaticFilesStorage``. Like Django's
``ManifestStaticFilesStorage``, it adds a content hash to the other static
files, but it leaves ``bundles/`` alone. Vite already hashed those files, and
they import each other by their Vite file names. A second, Django-hashed copy
would be loaded as a separate module (e.g. two preact instances).

Local development
~~~~~~~~~~~~~~~~~

With the development settings (``open_inwoner.conf.dev``) you can work in
either of two ways:

* **Dev server**: run ``npm run watch`` next to ``runserver``. This starts the
  Vite dev server on ``http://localhost:5173``. Django serves the assets from
  the dev server and adds Vite's hot reload client to the pages, so Sass and
  JavaScript changes appear in the browser without a reload or a rebuild.
* **Build output**: when the dev server isn't running, Django falls back to
  the output of the last ``npm run build``. You don't need to restart Django
  after a rebuild, because the manifest is re-read whenever it changes.

Django checks whether the dev server is running by trying to connect to port
5173, at most once a second (see ``open_inwoner.utils.vite.ViteAppClient``), so
you can start and stop ``npm run watch`` at any time.

Some things to keep in mind:

* The port is fixed (``strictPort`` in ``vite.config.js``): if 5173 is already
  in use, ``npm run watch`` fails instead of picking another port. If you
  change the port, also change ``_VITE_DEV_SERVER`` in
  ``src/open_inwoner/conf/dev.py``, which allows the dev server in the Content
  Security Policy.
* The dev server only switches on when ``DJANGO_VITE["default"]["dev_mode"]``
  is enabled, as it is in ``open_inwoner.conf.dev``. Other settings modules
  (e.g. ``docker`` and ``production``) always use the build output.
* Vite watches the project directory for changes, minus the directories
  listed under ``server.watch.ignored`` in ``vite.config.js``. If you hit the
  ``inotify`` watch limit (``ENOSPC`` errors), add the offending directory,
  such as a virtualenv with a different name, to that list.

.. _Vite: https://vite.dev/
.. _django-vite: https://github.com/MrBin99/django-vite


ElasticSearch
-------------

1. To start ElasticSearch, run the following command:

   .. code-block:: bash

        bin/start_elasticsearch.sh

   By default the script starts Elasticsearch with security enabled and the
   password ``elastic`` for the built-in ``elastic`` user (overridable via the
   ``ES_PASSWORD`` environment variable). The development settings default
   ``ES_USERNAME`` and ``ES_PASSWORD`` to ``elastic`` to match, so no extra
   configuration is needed for a standard local setup.

2. Then build the indices:

   .. code-block:: bash

        src/manage.py search_index --rebuild


Update installation
-------------------

When updating an existing installation:

1. Activate the virtual environment:

   .. code-block:: bash

       cd open-inwoner
       source env/bin/activate

2. Update the code and libraries:

   .. code-block:: bash

       git pull
       pip install -r requirements/dev.txt
       npm install

3. Rebuild the frontend, since the hashed bundle names change with every
   build (or run ``npm run watch`` instead, see `Frontend assets (Vite)`_):

   .. code-block:: bash

       npm run build

4. Update the statics and database:

   .. code-block:: bash

       python src/manage.py collectstatic --link
       python src/manage.py migrate

5. Update the ElasticSearch indices:

   .. code-block:: bash

       src/manage.py search_index --rebuild


Testsuite
---------

To run the test suite:

.. code-block:: bash

    python src/manage.py test open_inwoner

Configuration via environment variables
---------------------------------------

A number of common settings/configurations can be modified by setting
environment variables. You can persist these in your ``local.py`` settings
file or as part of the ``(post)activate`` of your virtualenv.

* ``SECRET_KEY``: the secret key to use. A default is set in ``dev.py``
* ``DIGID_MOCK``: determines if a mock-DigiD interface is to be shown on the frontend, if configured in the admin this has to be set to ``True`` to avoid switching to the mock-authentication by accident.
* ``EHERKENNING_MOCK``: determines if a mock-eHerkenning interface is to be shown on the frontend, if configured in the admin this has to be set to ``True`` to avoid switching to the mock-authentication by accident.

* ``DB_NAME``: name of the database for the project. Defaults to ``open_inwoner``.
* ``DB_USER``: username to connect to the database with. Defaults to ``open_inwoner``.
* ``DB_PASSWORD``: password to use to connect to the database. Defaults to ``open_inwoner``.
* ``DB_HOST``: database host. Defaults to ``localhost``
* ``DB_PORT``: database port. Defaults to ``5432``.

* ``SENTRY_DSN``: the DSN of the project in Sentry. If set, enabled Sentry SDK as
  logger and will send errors/logging to Sentry. If unset, Sentry SDK will be
  disabled.

* ``TWO_FACTOR_FORCE_OTP_ADMIN``: Enforce 2 Factor Authentication in the admin or not.
  Defaults to ``True``.
* ``TWO_FACTOR_PATCH_ADMIN``: Whether to use the 2 Factor Authentication login flow for
  the admin or not. Defaults to ``True``.

* ``ES_HOST``: Elasticsearch host URL. Defaults to ``http://localhost:9200``.
* ``ES_USERNAME``: Elasticsearch username for basic authentication. When both
  ``ES_USERNAME`` and ``ES_PASSWORD`` are set, the client will authenticate using
  HTTP basic auth. Leave unset to connect without authentication.
* ``ES_PASSWORD``: Elasticsearch password for basic authentication. See ``ES_USERNAME``.
