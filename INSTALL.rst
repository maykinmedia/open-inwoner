============
Installation
============

This installation is meant for developers of Open Inwoner Platform.
The project is developed in Python using the `Django framework`_. There are 3
sections below, focussing on developers, running the project using Docker and
hints for running the project in production.

.. _Django framework: https://www.djangoproject.com/


Development
===========


Prerequisites
-------------

You need the following libraries and/or programs:

* `Python`_ 3.9 or above
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

       $ git clone git@github.com:maykinmedia/open-inwoner.git
       $ cd open-inwoner

3. Install all required (backend) libraries.
   **Tip:** You can use the ``bootstrap.py`` script to install the requirements
   and set the proper settings in ``manage.py``. Or, perform the steps
   manually:

   .. code-block:: bash

       $ virtualenv env
       $ source env/bin/activate
       $ pip install -r requirements/dev.txt

4. Run third-party install commands:

   - Install the required browsers for `Playwright`_ end-to-end testing.

   .. code-block:: bash

       $ playwright install

.. _Playwright: https://playwright.dev/python/

5. Install and build the frontend libraries:

   .. code-block:: bash

       $ npm install
       or as an alternative: npm ci --legacy-peer-deps
       $ npm run build

6. Create the statics and database:

   .. code-block:: bash

       $ python src/manage.py collectstatic --link
       $ python src/manage.py migrate

7. Create a superuser to access the management interface:

   .. code-block:: bash

       $ python src/manage.py createsuperuser

8. You can now run your installation and point your browser to the address
   given by this command:

   .. code-block:: bash

       $ python src/manage.py runserver

9. Create a .env file with database settings. See dotenv.example for an example.

        $ cp dotenv.example .env


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

        $ bin/start_elasticsearch.sh

2. Then build the indices:

   .. code-block:: bash

        $ src/manage.py search_index --rebuild


Update installation
-------------------

When updating an existing installation:

1. Activate the virtual environment:

   .. code-block:: bash

       $ cd open-inwoner
       $ source env/bin/activate

2. Update the code and libraries:

   .. code-block:: bash

       $ git pull
       $ pip install -r requirements/dev.txt
       $ npm install
       or as an alternative: npm ci --legacy-peer-deps
       $ npm run build

3. Update the statics and database:

   .. code-block:: bash

       $ python src/manage.py collectstatic --link
       $ python src/manage.py migrate

4. Update the ElasticSearch indices:

   .. code-block:: bash

       $ src/manage.py search_index --rebuild


Testsuite
---------

To run the test suite:

.. code-block:: bash

    $ python src/manage.py test open_inwoner

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

Docker
======

The easiest way to get the project started is by using `Docker Compose`_.

1. Clone or download the code from `Github`_ in a folder like
   ``open-inwoner``:

   .. code-block:: bash

       $ git clone git@bitbucket.org:maykinmedia/open-inwoner.git
       Cloning into 'open-inwoner'...
       ...

       $ cd open-inwoner

2. Start the database and web services:

   .. code-block:: bash

       $ docker-compose up -d
       Starting open-inwoner_db_1 ... done
       Starting open-inwoner_web_1 ... done

   It can take a while before everything is done. Even after starting the web
   container, the database might still be migrating. You can always check the
   status with:

   .. code-block:: bash

       $ docker logs -f open-inwoner_web_1

3. Create an admin user. If different container names are shown above, use
   the container name ending with ``_web_1``:

   .. code-block:: bash

       $ docker exec -it open-inwoner_web_1 /app/src/manage.py createsuperuser
       E-mail address: admin@admin.com
       ...
       Superuser created successfully.

4. Point your browser to ``http://localhost:8000/`` to access the project's
   management interface with the credentials used in step 3.

   If you are using ``Docker Machine``, you need to point your browser to the
   Docker VM IP address. You can get the IP address by doing
   ``docker-machine ls`` and point your browser to
   ``http://<ip>:8000/`` instead (where the ``<ip>`` is shown below the URL
   column):

   .. code-block:: bash

       $ docker-machine ls
       NAME      ACTIVE   DRIVER       STATE     URL
       default   *        virtualbox   Running   tcp://<ip>:<port>

5. To shutdown the services, use ``docker-compose down`` and to clean up your
   system you can run ``docker system prune``.

.. _Docker Compose: https://docs.docker.com/compose/install/
.. _Github: https://github.com/maykinmedia/open_inwoner/


More Docker
-----------

If you just want to run the project as a Docker container and connect to an
external database, you can build and run the ``Dockerfile`` and pass several
environment variables. See ``src/open_inwoner/conf/docker.py`` for
all settings.

.. code-block:: bash

    $ docker build -t open_inwoner
    $ docker run \
        -p 8000:8000 \
        -e DATABASE_USERNAME=... \
        -e DATABASE_PASSWORD=... \
        -e DATABASE_HOST=... \
        --name open_inwoner \
        open_inwoner

    $ docker exec -it open_inwoner /app/src/manage.py createsuperuser

Staging and production
======================

Ansible is used to deploy test, staging and production servers. It is assumed
the target machine has a clean `Debian`_ installation.

1. Make sure you have `Ansible`_ installed (globally or in the virtual
   environment):

   .. code-block:: bash

       $ pip install ansible

2. Navigate to the project directory, and install the Maykin deployment
   submodule if you haven't already:

   .. code-block:: bash

       $ git submodule update --init

3. Run the Ansible playbook to provision a clean Debian machine:

   .. code-block:: bash

       $ cd deployment
       $ ansible-playbook <test/staging/production>.yml

For more information, see the ``README`` file in the deployment directory.

.. _Debian: https://www.debian.org/
.. _Ansible: https://pypi.org/project/ansible/


Settings
========

All settings for the project can be found in
``src/open_inwoner/conf``.
The file ``local.py`` overwrites settings from the base configuration.


Commands
========

Commands can be executed using:

.. code-block:: bash

    $ python src/manage.py <command>

There are no specific commands for the project. See
`Django framework commands`_ for all default commands, or type
``python src/manage.py --help``.

.. _Django framework commands: https://docs.djangoproject.com/en/dev/ref/django-admin/#available-commands


NLDS DesignTokens
=================

Generate a CSS file from JSON designtokens

    $ python src/manage.py shell < src/open_inwoner/generate_css.py
