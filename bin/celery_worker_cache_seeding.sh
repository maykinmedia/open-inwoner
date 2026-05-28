#!/bin/bash

if [ -d "env" ]; then
    . env/bin/activate
fi

set -e

OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-openinwoner-celery-cache-seeding}"

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}
# IO-bound tasks benefit from a higher fork count; tune with
# CELERY_CACHE_SEEDING_CONCURRENCY to match your deployment.
CONCURRENCY=${CELERY_CACHE_SEEDING_CONCURRENCY:-10}

# Must match the Django CACHE_SEEDING_QUEUE setting (default: "cache-seeding").
QUEUE=${CELERY_CACHE_SEEDING_QUEUE:-cache-seeding}
WORKER_NAME=${CELERY_CACHE_SEEDING_WORKER_NAME:-"${QUEUE}"@%n}

_binary=$(which celery)

if [[ "$ENABLE_COVERAGE" ]]; then
    _binary="coverage run $_binary"
fi

echo "Starting cache-seeding celery worker $WORKER_NAME with queue $QUEUE"
exec $_binary --workdir src --app "open_inwoner.celery" worker \
    -Q $QUEUE \
    -n $WORKER_NAME \
    -l $LOGLEVEL \
    -O fair \
    -c $CONCURRENCY \
    -E \
    --max-tasks-per-child=50
