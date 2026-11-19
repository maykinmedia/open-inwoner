.. _configuration_redis:

Securing Redis
==============

Open Inwoner uses Redis for its caches, which include user sessions, and as the
Celery task broker. The application trusts the data it reads from Redis, so
Redis must only be reachable by Open Inwoner itself. Anyone who can read from
or write to it can, among other things, read or tamper with sessions, poison
cached data and queue arbitrary background tasks.

Make sure no other party can connect to Redis, intercept the traffic to it, or
answer in its place.


Network isolation
-----------------

Do not expose Redis outside the deployment, and use a separate Redis instance
per installation. In shared environments, such as a multi-tenant Kubernetes
cluster or a shared Docker network, use network policies or firewall rules so
that only the Open Inwoner web and Celery processes can reach it.

Traffic to Redis is not encrypted (see :ref:`configuration_redis_settings`), so
it should not cross a network you don't fully control. Authentication alone
does not protect against a party that can intercept or modify the traffic.


Authentication
--------------

Enable Redis `AUTH or ACLs`_, preferably with a dedicated user per
installation, and include the credentials in the connection settings:

.. code-block:: bash

    CACHE_DEFAULT=open-inwoner:<password>@redis.example.internal:6379/0
    CELERY_BROKER_URL=redis://open-inwoner:<password>@redis.example.internal:6379/1

.. _AUTH or ACLs: https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/


.. _configuration_redis_settings:

Connection settings
-------------------

The following environment variables configure the connections, see
:doc:`02_env_vars` for details:

``CACHE_DEFAULT``
    The default cache, which also holds sessions and login attempts, in
    ``host:port/db`` format (optionally preceded by ``user:password@``). The
    ``redis://`` scheme is added by the application, so TLS is not supported
    for the caches.

``CACHE_NOTIFICATION_THROTTLE_LOCATION``
    The Redis cache used to rate limit notifications, as a full URL. It always
    uses the same settings as the default cache, and defaults to its location.

``CELERY_BROKER_URL``
    The Celery broker, as a full URL (``redis://`` or ``rediss://`` for TLS).

Always set these explicitly. The defaults point to Redis on ``localhost``,
where any other process on the same host or pod could answer.

We recommend using a separate Redis database for the Celery broker, so that
clearing the cache does not also remove queued tasks.


Persistence and backups
-----------------------

Redis persistence files (RDB and AOF) and their backups contain sessions and
cached data. Treat them as sensitive, and do not restore them from untrusted
sources.


Rotating ``SECRET_KEY``
-----------------------

Cached data is signed with ``SECRET_KEY``. The application ignores cached data
with an invalid signature, treats it as missing and logs a
``cache_signature_invalid`` warning. When rotating the key, set the previous
value as ``SECRET_KEY_FALLBACK``. Otherwise, all cached data is discarded at
once: every user is logged out, and the caches are rebuilt, which temporarily
puts more load on the connected systems.

Each refused value is also counted in the OpenTelemetry metric
``oip.cache.signature_invalid``. Refused values without a key rotation can mean
that someone is writing to Redis, or that processes sharing the same Redis
database use different values for ``SECRET_KEY``. We recommend alerting on any
increase of this metric outside a planned key rotation.
