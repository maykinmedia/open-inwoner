.. _installation_docker_compose:

==============
Docker Compose
==============

We include a compose stack for development purposes and for trying out OIP on
your own machine.

The `docker_compose.yml` defines 'convenience' settings, meaning that that no
additional configuration is needed to run the app. It is **not** suitable
for production.

This comes in three flavours:

- The base stack (``docker compose up``, `Getting started`_ below) -- just
  the app itself plus its own database and Mailpit, with none of the
  external services it can integrate with configured. Enough for most local
  development and for trying OIP out.
- The full stack (``bin/stack.sh up``,
  :ref:`installation_docker_compose_full_stack` below) -- the base stack
  plus every Common Ground service it talks to (Keycloak, Open Zaak, the
  Objects/Objecttypes APIs, the Haal Centraal BRP mock, Open Klant, Open
  Afval) and an observability stack, all pre-wired together. Use this for
  integration/end-to-end testing of anything that touches those services --
  OIDC login, case management, BRP lookups, and so on.
- The full stack, minus the app itself (``bin/stack.sh up --localhost``,
  :ref:`installation_docker_compose_host_mode` below) -- everything above
  except Open Inwoner, which you then run yourself on the host. Use this
  when you're working on Open Inwoner's own code and want a debugger and
  autoreload, while still testing against every other service for real.


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

3. Create the shared ``open-inwoner-dev`` Docker network. It's declared as
   ``external: true`` in every compose file (root and satellite alike) so
   that bringing up several of them together never races over who
   creates/owns it -- see :ref:`installation_docker_compose_full_stack`
   below. This is a one-off step -- the script is a no-op if the network
   already exists:

   .. code:: bash

        bin/ensure_dev_network.sh

4. Start the docker containers with ``docker compose up``. If you want to run the
   containers in the background, add the ``-d`` option.

5. Create a super-user:

   .. code:: bash

        sudo docker exec -it open-inwoner-web src/manage.py createsuperuser

6. Navigate to ``http://127.0.0.1:8000/admin/`` and use the credentials created
   above to log in.

7. To stop the containers, press *CTRL-C* or if you used the ``-d`` option:

   .. code:: bash

        docker compose stop

The stack also includes `Mailpit <https://github.com/axllent/mailpit>`_, an
SMTP server that catches every outgoing email instead of actually sending it.
``EMAIL_HOST``/``EMAIL_PORT`` already point the app at it, so no extra setup
is needed -- browse to http://localhost:8025/ to see anything the app has
sent (password resets, notifications, etc.).


.. _installation_docker_compose_full_stack:

Running the full stack
=======================

On top of the base app stack, several Common Ground components each have
their own compose file under ``docker/`` so you can exercise a fully wired
local environment -- OIDC login, Open Zaak, the Objects/Objecttypes APIs,
the Haal Centraal BRP mock, Open Klant and Open Afval -- without pointing at
shared acceptance environments:

- ``docker/docker-compose.keycloak.yml`` -- Keycloak, the local OIDC provider
- ``docker/docker-compose.open-zaak.yml`` -- Open Zaak (Zaken, Catalogi,
  Documenten and Besluiten APIs)
- ``docker/docker-compose.objects-apis.yml`` -- the Objects API and
  Objecttypes API
- ``docker/docker-compose.hc-brp-mock.yml`` -- the Haal Centraal BRP
  ``personen-mock``
- ``docker/docker-compose.openklant.yml`` -- Open Klant (Klantinteracties and
  Contactmomenten APIs)
- ``docker/docker-compose.openafval.yml`` -- `Open Afval
  <https://github.com/maykinmedia/open-afval>`_, the waste collection API
  backing the "Mijn afval" CMS page
- ``docker/docker-compose.observability.yml`` -- Grafana/Loki/Prometheus/an
  OTel collector, for inspecting the app's own logs, metrics and traces (see
  `Testing OpenTelemetry Observability`_ below)

All of these attach to the same external ``open-inwoner-dev`` network as the
main app stack (see `Getting started`_, step 3) and publish internal DNS
aliases such as ``keycloak.internal``, ``openzaak.internal``,
``openklant.internal``, ``objects.internal``, ``objecttypes.internal`` and
``openafval.internal``. ``docker/setup_configuration/data.yaml`` -- which
``web-init`` applies on its first run (see below) -- already points its
ZGW/OpenKlant/Objects/Haal Centraal service configuration at those aliases
(Keycloak's OIDC endpoints are the exception, see below), so once those
stacks are up the app is pre-configured to talk to them without any manual
admin work. Open Afval is the exception to that: there's no
``setup_configuration`` step for ``MijnAfvalConfig`` yet (the same gap Haal
Centraal BRP had until one was added), so wiring the "Mijn afval" page up to
the ``openafval-web`` service still means creating the ``zgw_consumers``
``Service`` and ``MijnAfvalConfig`` by hand in the admin.

Keycloak's OIDC endpoints are the one exception to "server-side only": the
authorization endpoint is where your own *browser* gets redirected to log
in, not just something the ``web`` container calls, so it has to resolve
from your host too. That's why ``data.yaml``'s OIDC endpoints point at
``keycloak.open-inwoner.local`` instead of ``keycloak.internal`` -- add it
to your hosts file, pointing at Keycloak's published port on localhost:

.. code:: bash

     echo '127.0.0.1 keycloak.open-inwoner.local' | sudo tee -a /etc/hosts

Without it, the OIDC login redirect fails to resolve as soon as your
browser is sent to Keycloak.

The easiest way to bring all of it up is:

.. code:: bash

     bin/stack.sh up

which creates the shared network, then starts almost everything else at once
in the background -- the satellites, the observability stack, the app's own
database/redis/elasticsearch, and an app image rebuild -- since none of it
needs to wait on any of the rest of it yet (``web-init`` writes
``Service``/``OIDCProvider``/config rows pointing at the satellites, but
never actually calls them, so it doesn't need any of them reachable to run).
It waits for the database/redis/elasticsearch and the image build to finish,
starts the main app stack, then waits for Open Zaak/Objects before
triggering a ZGW data import, which does call them for real. Run
``bin/stack.sh up --logs`` to also follow the app's logs afterwards, and
``bin/stack.sh down`` (optionally with ``-v`` to also wipe volumes) to bring
it all down again. Anything else, e.g. ``bin/stack.sh ps`` or
``bin/stack.sh exec web bash``, is forwarded straight to ``docker compose``
with the right ``-f`` chain already applied.

``bin/stack.sh up`` also overrides ``OTEL_SDK_DISABLED`` to ``false`` for the
app containers (it defaults to ``true`` -- disabled -- everywhere else, per
`Testing OpenTelemetry Observability`_ below), since it brings up the
observability stack itself and there's no point running Grafana/Loki/
Prometheus with nothing feeding them.

The script is a thin wrapper around plain ``docker compose`` invocations --
read it for the exact commands if you want to bring stacks up individually,
add ``-f`` flags of your own, or otherwise deviate from the default. Two
details it takes care of that are easy to get wrong by hand:

- ``docker/docker-compose.keycloak.yml`` resolves its own relative path
  (``./keycloak/fixtures/realm.json``) against its *own* directory rather
  than the repository root, so it can't be combined with the other satellite
  files via a plain ``-f a -f b`` chain -- doing so would silently bind-mount
  an empty directory instead of the realm fixture.
  ``docker-compose.dev.yml`` (which the script uses) works around this with
  Compose's ``include:`` feature, which resolves each included file's paths
  relative to that file's own location.
- ``web-init`` only runs ``setup_configuration`` once per database (see the
  comment in ``bin/setup_configuration.sh``): several steps -- OpenZaak,
  KlantenSysteem, Users -- converge their fields back to whatever
  ``data.yaml`` says on *every* run, which would silently undo any changes
  made through the admin on a plain restart. Run ``bin/stack.sh
  reset-config`` (then ``bin/stack.sh up`` if you want the app started too)
  to force a re-run, e.g. after changing ``data.yaml``.

Once it's up, the individual services are also reachable from your host
machine:

======================  ============================  ==================
Service                 URL                           Credentials
======================  ============================  ==================
Keycloak admin          http://localhost:8080/        admin / admin
Open Zaak admin         http://localhost:8002/admin/  admin / admin
Objecttypes API admin   http://localhost:8003/admin/  admin / admin
Objects API admin       http://localhost:8004/admin/  admin / admin
Open Klant admin        http://localhost:8338/admin/  admin / admin [1]_
Open Afval admin        http://localhost:8339/admin/  admin / admin [1]_
Haal Centraal BRP mock  http://localhost:5010/        --
Grafana                 http://localhost:3000/        --
Prometheus              http://localhost:9090/        --
Loki (readiness)        http://localhost:3100/ready   --
======================  ============================  ==================

.. [1] Open Klant's and Open Afval's images don't support the
   ``*_SUPERUSER_*``/``KEYCLOAK_ADMIN*`` environment variables the other
   admins use -- both instead bring up a one-shot ``*-seed`` container that
   ``loaddata``\ s an ``accounts.user`` fixture (``docker/openklant/fixtures/db.json``
   and ``docker/openafval/fixtures/db.json``).

Logging in to Open Inwoner itself, at either ``http://localhost:8000/`` or
the nginx-fronted ``http://localhost:9000/`` (both work equally well, see
below), goes through the same Keycloak test realm for every login type:

=============  ====================================================  ===============================================
Log in as      URL                                                   Notes
=============  ====================================================  ===============================================
Admin (staff)  http://localhost:8000/admin/                          Click "Login with OIDC", Keycloak admin / admin
DigiD          http://localhost:8000/digid-oidc/authenticate/        any BSN test user
eHerkenning    http://localhost:8000/eherkenning-oidc/authenticate/  any eHerkenning test user
eIDAS          http://localhost:8000/eidas-oidc/authenticate/        any eIDAS test user
=============  ====================================================  ===============================================

See ``docker/keycloak/README.md`` for the full list of test users (DigiD
machtigen, eHerkenning bewindvoering/vestiging, eIDAS natural
person/company, etc.) and which claims each one carries.

The realm's SSO session lifetimes are deliberately short (``ssoSessionIdleTimeout``:
60s, ``ssoSessionMaxLifespan``: 5 minutes) so that switching between the test
users listed in ``docker/keycloak/README.md`` reliably prompts for a fresh
login instead of silently reusing whichever user is still logged in at
Keycloak. If you need to switch users faster than that, log out at Keycloak
(or use a private/incognito window) rather than relying on the timeout alone
-- a still-active session is reused with no prompt at all.

.. _installation_docker_compose_host_mode:

Running Open Inwoner on the host
=================================

Running Open Inwoner itself in Docker is a slow loop for working on its own
code: every change needs a rebuild, and there's no debugger or autoreload.
``bin/stack.sh up --localhost`` keeps every satellite and backing service
(database, Redis, Elasticsearch, and everything listed above) running in
Docker exactly as with a normal ``bin/stack.sh up``, but skips starting Open
Inwoner itself so you can run it yourself from a virtualenv instead --
generating its host-mode config, migrating, seeding (``setup_configuration``,
the ZGW import, the search index) and printing the command to start it,
the same way a normal ``bin/stack.sh up`` does for the Dockerized app:

.. code:: bash

     bin/stack.sh up --localhost

Once it finishes, start the app itself:

.. code:: bash

     python src/manage.py runserver

Postgres, Redis and Elasticsearch are published on 5433, 6380 and 9202, not
their usual 5432/6379/9200, so they don't collide with a native install on
the host. ``conf.dev`` defaults ``DB_PORT``/``CACHE_DEFAULT``/
``CELERY_BROKER_URL``/``ES_HOST`` to those ports, since ``up --localhost`` is
the standard way to run OIP outside Docker -- no env vars to export. If
you're *not* using ``up --localhost`` (e.g. a native Postgres/Redis/
Elasticsearch install instead), override those in ``local.py``. This only
affects the host: ``conf.docker``, used inside the containers themselves,
doesn't import ``conf.dev`` and is unaffected either way.

``docker/setup_configuration/data.yaml`` and its ``openzaak_config.json``
fixture are themselves generated -- from ``data.yaml.j2``/
``openzaak_config.json.j2``, the actual source of truth, which use
Jinja2 placeholders for the satellites' addresses instead of hardcoding
either mode's values. ``bin/generate_setup_configuration.py`` renders both
templates twice: once with Docker-internal addresses into the paths above
(committed to git, since plain ``docker compose up`` reads them directly
with no generation step of its own -- re-run this script and commit the
result whenever you edit a ``.j2`` template), and once with ``localhost``
equivalents on the satellites' published ports into the gitignored
``docker/setup_configuration/.host/`` folder, which is what ``up
--localhost`` actually feeds to ``setup_configuration``/``loaddata``. Run it
by hand if you only edited a template and don't need a full re-seed --
``up --localhost`` already runs it automatically.

Like ``web-init`` in the full stack, ``setup_configuration`` and the
``openzaak_config.json`` load only run once per database -- a marker file in
that same ``.host/`` folder records it, so re-running ``up --localhost``
(e.g. after a restart) doesn't overwrite any admin changes you've made
locally. ``bin/stack.sh reset-config`` clears that marker (and web-init's)
to force it to run again, e.g. after editing ``data.yaml``. Migrations, the
ZGW import and the search index rebuild aren't gated by that marker and run
on every ``up --localhost``, same as the full stack.

The Keycloak hosts-file entry from above is still needed. Once
``runserver`` is up, the same login table above applies unchanged -- Open
Inwoner runs on ``http://localhost:8000/`` either way.

Bring the satellites down again the same way as the full stack:

.. code:: bash

     bin/stack.sh down

A few things worth knowing about this mode:

- ``.env`` is read by both ``python-dotenv`` (loaded by the app on startup)
  and by Docker Compose's own ``${VAR:-default}`` substitution. Prefer
  ``src/open_inwoner/conf/local.py`` for settings that only matter to the
  app itself, and leave ``.env`` for Compose-side settings, so the two
  don't collide.
- Redis is a required service for host mode, same as Postgres/Elasticsearch --
  not just as Celery's broker, but because async tasks (e.g. login cache
  warm-up) hand their results back to the web process through the shared
  ``default``/``axes`` caches, which are Redis-backed.
- Elasticsearch isn't required for the app to start, but saving a product or
  CMS page in the admin will error while it's down, since indexing happens
  synchronously by default. Set ``ELASTICSEARCH_DSL_AUTOSYNC=False`` if you
  want to work without it.
- Outgoing mail goes to a queue, not straight out, so a Celery worker
  (``bin/celery_worker.sh``) needs to be running for it to actually reach
  Mailpit. Same worker also handles notification webhooks and login cache
  warm-up.

Testing OpenTelemetry Observability
===================================

``bin/stack.sh up`` (see :ref:`installation_docker_compose_full_stack` above)
already includes the observability stack and sets ``OTEL_SDK_DISABLED`` to
False for you -- if you're using it, there's nothing else to do; open
http://localhost:3000 for Grafana.

Open Zaak, Open Klant, the Objects/Objecttypes APIs and Open Afval export to
the same collector too (they're built on the same shared
``open_api_framework``/``maykin_common`` base as this app), each tagged with
its own ``OTEL_SERVICE_NAME`` so they're distinguishable in Grafana. The
Haal Centraal BRP mock is the one exception -- it's a different (.NET)
stack entirely with no OpenTelemetry support.

Without ``bin/stack.sh``, to test the OpenTelemetry setup and view metrics in
Grafana:

1. Start the observability stack first:

   .. code:: bash

        bin/start_observability.sh

2. Start the application with OpenTelemetry enabled:

   .. code:: bash

        OTEL_SDK_DISABLED=false docker compose up

3. Access Grafana dashboard at http://localhost:3000 to view metrics

The observability stack includes monitoring and metrics collection for the application
performance and behavior. The easiest way to see if this is working is to navigate to
the "Drilldown > Metrics" item in the left menu and filter by the ``otel_`` prefix.

Traces go to Grafana Tempo (the ``tempo`` service, queryable from Grafana's
"Tempo" datasource) and application/container logs go to Loki via Promtail --
see ``docker/observability/README.md`` for sample LogQL queries and how the
two are linked (a log line's ``trace_id`` field becomes a clickable link to
its trace).
