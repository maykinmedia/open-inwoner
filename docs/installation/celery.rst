.. _installation_celery:

======
Celery
======

Open Inwoner uses `Celery <https://docs.celeryq.dev/>`_ for background processing:
handling ZGW notifications, importing data, sending digest emails and seeding the
cache for the case list.


Worker topology
===============

Workers are started with ``bin/celery_worker.sh``. The script is configured through
environment variables that are read by the shell script itself, **not** by Django
settings, so they must be set on the worker container:

``CELERY_WORKER_QUEUE``
    Queue the worker consumes (``-Q``). Defaults to ``celery``.

``CELERY_WORKER_CONCURRENCY``
    Number of child processes (``-c``). Defaults to ``4``.

``CELERY_WORKER_NAME``
    Worker node name, used in monitoring. Defaults to ``<queue>@%n``.

``CELERY_LOGLEVEL``
    Log level. Defaults to ``INFO``.

Besides workers there are two supporting processes:

* ``bin/celery_beat.sh`` runs the scheduler for periodic tasks. Run **exactly one**
  instance; multiple beats will schedule duplicate tasks.
* ``bin/celery_monitor.sh`` records task events for monitoring.


Cache seeding for the case list
===============================

Fetching a user's zaken from the ZGW APIs is slow when nothing is cached: the case
list runs a time-budgeted pipeline (see ``case_list_fetch_timeout`` in the admin) and
drops whatever does not finish in time. To avoid this, a cache warm-up task is
dispatched when a user logs in, so the data is usually already in Redis by the time
the user opens "Mijn zaken".

That task competes with all other background work for worker slots. If a long-running
task (a data import, a batch of notifications) occupies the worker pool, the warm-up
runs too late to be useful. The queue it is sent to is configured with:

.. code-block:: bash

    CACHE_SEEDING_QUEUE=celery

This defaults to Celery's built-in ``celery`` queue, so a single-worker deployment
works without any extra configuration.


Recommended production setup
----------------------------

For production, dedicate a separate worker to the cache-seeding queue. The warm-up
task is IO-bound (it waits on HTTP responses), so it can run at a much higher
concurrency than the default worker pool:

* Run an additional worker with ``CELERY_WORKER_QUEUE=low-latency`` and
  ``CELERY_WORKER_CONCURRENCY=10``.
* Set ``CACHE_SEEDING_QUEUE=low-latency`` on the **web** containers, which are the
  ones dispatching the task.

The ``celery-low-latency`` service in ``docker-compose.yml`` is a working reference
for this layout.

.. warning::

   ``CACHE_SEEDING_QUEUE`` must name a queue that a worker actually consumes. Celery
   accepts messages for a queue nobody listens to without any error: the tasks pile
   up in Redis indefinitely, no warm-up ever runs, and the only symptom is that case
   lists stay slow and occasionally incomplete.

   After changing the setting, verify that the queue is being consumed:

   .. code-block:: bash

       celery -A open_inwoner.celery inspect active_queues

   The output must list the configured queue for at least one worker. Worker health
   can be checked with ``maykin-common worker-health-check --skip-ping``, which is
   also used as the container health check in ``docker-compose.yml``.
