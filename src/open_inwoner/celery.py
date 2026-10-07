from django.conf import settings

from celery import Celery
from maykin_common.health_checks.celery.probes import EventLoopProbe
from maykin_common.logging.celery import setup_celery_structlog

from .setup import setup_env

setup_env()

app = Celery("open_inwoner")
app.config_from_object("django.conf:settings", namespace="CELERY")

setup_celery_structlog()

app.conf.ONCE = {
    "backend": "celery_once.backends.Redis",
    "settings": {
        "url": settings.CELERY_BROKER_URL,
        "default_timeout": 60 * 60,  # one hour
    },
}

app.autodiscover_tasks()


app.steps["worker"].add(EventLoopProbe)


@app.task
def trigger_exception():
    """Trigger an exception for debugging purposes."""
    return 1 / 0


@app.task(ignore_result=True)
def beat_health_sentinel():
    """
    No-op task scheduled at a high frequency purely so celery-beat has
    something to publish regularly.

    ``maykin_common.health_checks.celery.probes.on_beat_task_published``
    touches beat's liveness file whenever *any* scheduled task is published,
    so without this, that file is only touched as often as the
    least-frequent real periodic task in CELERY_BEAT_SCHEDULE fires --
    leaving beat's healthcheck unable to pass for that long after every
    (re)start.
    """
