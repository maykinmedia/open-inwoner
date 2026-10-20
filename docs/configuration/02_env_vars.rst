.. _configuration_env_vars:

Environment variables
=====================

.. config-all-params::
   :exclude-groups: Setup-configuration
   :exclude-params: DISABLE_2FA, PROFILE

.. _configuration_env_vars_scripts:

Container start scripts
-----------------------

The variables below are read by the start scripts in the Docker image
(``bin/docker_start.sh``, ``bin/celery_*.sh``) or by the libraries they start,
not by the Django settings, so they are not listed above.

Web server (``bin/docker_start.sh``)
""""""""""""""""""""""""""""""""""""

``PORT``
    Port uWSGI listens on. Defaults to ``8000``.

``STATIC_ROOT_VOLUME``
    If set, the static files are copied to this directory on startup, e.g. a
    volume shared with a reverse proxy that serves them.

``UWSGI_PROCESSES``
    Number of uWSGI worker processes. Defaults to ``4``.

``UWSGI_THREADS``
    Number of threads per process. Defaults to ``8``.

``UWSGI_HTTP_KEEPALIVE``
    Enable HTTP keep-alive. Defaults to ``1``.

``UWSGI_HTTP_TIMEOUT``
    HTTP timeout in seconds. Defaults to ``120``.

``UWSGI_HARAKIRI``
    Kill requests that take longer than this many seconds. Defaults to ``125``,
    slightly longer than ``UWSGI_HTTP_TIMEOUT``.

``UWSGI_MAX_REQUESTS``
    Recycle a worker after this many requests. Defaults to ``100``.

``UWSGI_POST_BUFFERING``
    Buffer size for POST request bodies in bytes. Defaults to ``8192``.

``UWSGI_BUFFER_SIZE``
    Internal uWSGI buffer size in bytes. Defaults to ``65535``. Increase this if
    requests with large headers (e.g. big cookies) are rejected.

Any other ``UWSGI_*`` variable is passed on to uWSGI as well, see the
`uWSGI documentation <https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#environment-variables>`_.

Celery (``bin/celery_*.sh``)
""""""""""""""""""""""""""""

``CELERY_WORKER_QUEUE``, ``CELERY_WORKER_CONCURRENCY``, ``CELERY_WORKER_NAME``
and ``CELERY_LOGLEVEL`` are described in :ref:`installation_celery`.

OpenTelemetry
"""""""""""""

Open Inwoner uses the OpenTelemetry SDK, which is configured with the standard
``OTEL_*`` variables, see the
`OpenTelemetry SDK configuration <https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/>`_.
The most relevant ones are:

``OTEL_SDK_DISABLED``
    Set to ``true`` to disable OpenTelemetry completely, e.g. when no collector
    is available. OpenTelemetry is enabled by default.

``OTEL_SERVICE_NAME``
    Name the telemetry is reported under. Each start script sets its own
    default: ``openinwoner-web``, ``openinwoner-celery-worker``,
    ``openinwoner-celery-beat`` and ``openinwoner-celery-monitor``. Set a
    distinct value per component if you override it.

``OTEL_EXPORTER_OTLP_ENDPOINT``, ``OTEL_EXPORTER_OTLP_HEADERS``
    Where to send the telemetry, and e.g. the authentication header for the
    collector.
