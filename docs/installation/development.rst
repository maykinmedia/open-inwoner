.. _installation_development:

===========
Development
===========

Prerequisites
-------------

You need the following libraries and/or programs:

* `Python`_ 3.11 or above
* Python `Virtualenv`_ and `Pip`_
* `PostgreSQL`_ 10 or above with PostGIS extension
* `Node.js`_
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

   - Or as an alternative:

   .. code-block:: bash

       npm ci --legacy-peer-deps
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

**Note:** You can run watch-tasks to compile `Sass`_ to CSS and `ECMA`_ to JS
using ``npm run watch``.

.. _ECMA: https://ecma-international.org/
.. _Sass: https://sass-lang.com/


ElasticSearch
-------------

1. To start ElasticSearch, run the following command:

   .. code-block:: bash

        bin/start_elasticsearch.sh

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
       or as an alternative: npm ci --legacy-peer-deps
       npm run build

3. Update the statics and database:

   .. code-block:: bash

       python src/manage.py collectstatic --link
       python src/manage.py migrate

4. Update the ElasticSearch indices:

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
