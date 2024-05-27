#!/bin/sh

. env/bin/activate

exec celery --workdir src -A "open_inwoner" events -l info --camera django_celery_monitor.camera.Camera --frequency=2.0 &
exec celery --workdir src -A "open_inwoner" worker -E --max-tasks-per-child=50 -l info -B --scheduler django_celery_beat.schedulers:DatabaseScheduler
