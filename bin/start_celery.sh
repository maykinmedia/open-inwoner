#!/bin/sh

exec celery -A "src.open_inwoner" events -l info --camera django_celery_monitor.camera.Camera --frequency=2.0 &
exec celery -A "src.open_inwoner" worker -E --max-tasks-per-child=50 -l info -B --scheduler django_celery_beat.schedulers:DatabaseScheduler
