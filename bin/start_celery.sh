#!/bin/sh

. env/bin/activate

LOGLEVEL=${CELERY_LOGLEVEL:-INFO}
CONCURRENCY=${CELERY_WORKER_CONCURRENCY:-1}

exec celery --workdir src -A "open_inwoner" events -l info --camera django_celery_monitor.camera.Camera --frequency=2.0 &
exec celery --workdir src -A "open_inwoner" worker -l $LOGLEVEL -c $CONCURRENCY -E --max-tasks-per-child=50 -l info -B --scheduler django_celery_beat.schedulers:DatabaseScheduler
