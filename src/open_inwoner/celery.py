import logging  # noqa: TID251 - correct use to replace stdlib logging
import logging.config  # noqa: TID251 - correct use to replace stdlib logging

from django.conf import settings

import structlog
from celery import Celery
from celery.signals import setup_logging
from maykin_common.config import config
from maykin_common.health_checks.celery.probes import EventLoopProbe

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
@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):
    formatter = config("LOG_FORMAT_CONSOLE", default="json")
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                    "foreign_pre_chain": [
                        structlog.contextvars.merge_contextvars,
                        structlog.processors.TimeStamper(fmt="iso"),
                        structlog.stdlib.add_logger_name,
                        structlog.stdlib.add_log_level,
                        structlog.stdlib.PositionalArgumentsFormatter(),
                    ],
                },
                "plain_console": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(),
                    "foreign_pre_chain": [
                        structlog.contextvars.merge_contextvars,
                        structlog.processors.TimeStamper(fmt="iso"),
                        structlog.stdlib.add_logger_name,
                        structlog.stdlib.add_log_level,
                        structlog.stdlib.PositionalArgumentsFormatter(),
                    ],
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter,
                },
            },
            "loggers": {
                "open_inwoner": {
                    "handlers": ["console"],
                    "level": "INFO",
                },
                "django_structlog": {
                    "handlers": ["console"],
                    "level": "INFO",
                },
            },
        }
    )


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
