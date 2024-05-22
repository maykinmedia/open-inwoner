.. _install_docker_compose:

============================
Install using Docker Compose
============================

We include a compose stack for development purposes and for trying out OIP on
your own machine.

The `docker_compose.yml` defines 'convenience' settings, meaning that that no
additional configuration is needed to run the app. It is **not** suitable
for production.


Getting started
===============

1. Clone the repository

   .. code:: bash

        git clone git@github.com:maykinmedia/open-inwoner.git

2. Optionally, you you can initialize the database on first startup with an SQL dump
   by adding it to ``docker-init-db.sql/``. In order to create a user for the database,
   add a ``.sql`` script in the same directory with the following content:

   .. code::

        DO
        $do$
        BEGIN
            IF NOT EXISTS ( SELECT FROM pg_roles WHERE rolname = 'open_inwoner') THEN
                CREATE USER open_inwoner;
            END IF;
        END
        $do$;

    Choose the rolname/user name depending on the owner of the database in the dump
    you're loading in.

    Make sure you get the quotes right: ``rolname`` requires single quotes. If you
    happen to have a ``USER`` name containing dashes, it must be referenced in double
    quotes (``"open-inwoner-test"``).

3. Start the docker containers with ``docker compose up``. If you want to run the
   containers in the background, add the ``-d`` option.

4. Create a super-user:

   .. code:: bash

        sudo docker exec -it open-inwoner-web src/manage.py createsuperuser

5. Navigate to ``http://127.0.0.1:8000/admin/`` and use the credentials created
   above to log in.

6. To stop the containers, press *CTRL-C* or if you used the ``-d`` option:

   .. code:: bash

        docker compose stop
