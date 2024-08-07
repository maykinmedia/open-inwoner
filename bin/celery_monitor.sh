#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

# This monitors the tasks executed by Celery. The Celery worker needs to be
# started with the -E option to sent out the events.

echo "Starting celery events"
exec celery --workdir src --app "open_inwoner.celery" events \
    -l $LOGLEVEL \
    --camera django_celery_monitor.camera.Camera \
    --frequency=2.0
