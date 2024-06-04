#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}
CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-1}

QUEUE=${1:-${CELERY_WORKER_QUEUE:=celery}}
WORKER_NAME=${2:-${CELERY_WORKER_NAME:="${QUEUE}"@%n}}

_binary=$(which celery)

if [[ "$ENABLE_COVERAGE" ]]; then
    _binary="coverage run $_binary"
fi

echo "Starting celery worker $WORKER_NAME with queue $QUEUE"
exec $_binary --workdir src -A "open_inwoner" events -l info --camera django_celery_monitor.camera.Camera --frequency=2.0 &
exec $_binary --workdir src -A "open_inwoner" worker -l $LOGLEVEL -c $CONCURRENCY -Q $QUEUE -n $WORKER_NAME -E --max-tasks-per-child=50 -l info -B --scheduler django_celery_beat.schedulers:DatabaseScheduler
