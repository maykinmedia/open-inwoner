.. _installation_health_checks:

=============
Health Checks
=============

Open Inwoner provides several health check endpoints for monitoring and orchestration
purposes. These endpoints allow you to verify the application's health and readiness
in different deployment scenarios.


Available Endpoints
===================

``/_healthz/``
--------------

Reports all configured checks, including:

* Database connection and permissions
* Configured caches
* Verification that all migrations have been executed

This is the most expensive check and suitable for the **Kubernetes startup probe**.

``/_healthz/livez/``
--------------------

The cheapest check - it does not check any dependencies like the database or caches.

This endpoint is extremely suitable for:

* HTTP **liveness probe** in Kubernetes
* Docker engine health check

``/_healthz/readyz/``
---------------------

A check slightly more expensive than the liveness subset. It verifies:

* Database connection
* Default cache connections

This endpoint is suitable for the **readiness probe** in Kubernetes.


Docker Compose Configuration
=============================

Docker Compose supports health checks via the ``healthcheck`` directive. Use the
``/_healthz/livez/`` endpoint for basic health monitoring:

.. code-block:: yaml

    services:
      web:
        image: maykinmedia/open-inwoner:latest
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:8000/_healthz/livez/"]
          interval: 30s
          timeout: 5s
          retries: 3
          start_period: 40s

.. note::
   Docker Compose does not have separate liveness/readiness/startup probes like
   Kubernetes. The ``healthcheck`` directive serves as a general health check.


Kubernetes Configuration
=========================

Kubernetes provides three distinct probe types that can use different health check
endpoints:

Startup Probe
-------------

Use ``/_healthz/`` for the startup probe to ensure the application is fully initialized:

.. code-block:: yaml

    startupProbe:
      httpGet:
        path: /_healthz/
        port: 8000
      failureThreshold: 45
      periodSeconds: 10

Liveness Probe
--------------

Use ``/_healthz/livez/`` for the liveness probe to detect if the application needs
to be restarted:

.. code-block:: yaml

    livenessProbe:
      httpGet:
        path: /_healthz/livez/
        port: 8000
      initialDelaySeconds: 60
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3

Readiness Probe
---------------

Use ``/_healthz/readyz/`` for the readiness probe to control traffic routing:

.. code-block:: yaml

    readinessProbe:
      httpGet:
        path: /_healthz/readyz/
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3


Response Format
===============

All health check endpoints return an overview of the checks that have passed or failed.
The response format depends on the ``Accept`` header:

* ``text/html``: Human-readable overview (default for browsers)
* ``application/json``: Machine-readable format (for monitoring tools)

You can force JSON output by appending ``?format=json`` to any health check URL.

HTTP Status Codes
-----------------

* ``200 OK``: All checks passed
* ``500 Server Error``: One or more checks failed

Troubleshooting
---------------

If health checks fail, examine the response body for details:

.. code-block:: bash
    curl -H "Accept: application/json" http://your-open-inwoner/_healthz/?format=json
