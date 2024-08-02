#!/bin/bash

set -e

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}

mkdir -p celerybeat

# Adding the database scheduler will also convert the CELERY_BEAT_SCHEDULE to
# database entries.

echo "Starting celery beat"
exec celery --workdir src --app "open_inwoner.celery" beat \
    -l $LOGLEVEL \
    -s ../celerybeat/beat \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --pidfile=  # empty on purpose, see https://github.com/open-formulieren/open-forms/issues/1182
