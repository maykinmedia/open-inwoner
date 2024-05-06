from django.conf import settings

from celery import Celery
from celery.signals import setup_logging
from celery_once import QueueOnce  # noqa

from .setup import setup_env

setup_env()

app = Celery("open_inwoner")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.ONCE = {
    "backend": "celery_once.backends.Redis",
    "settings": {
        "url": settings.CELERY_BROKER_URL,
        "default_timeout": 60 * 60,  # one hour
    },
}

app.autodiscover_tasks()


# Use django's logging settings as these are reset by Celery by default
@setup_logging.connect()
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig

    dictConfig(settings.LOGGING)
