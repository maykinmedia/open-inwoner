from django.conf import settings

from .celery import app as celery_app  # noqa

__version__ = settings.RELEASE
__author__ = "Maykin Media"
__homepage__ = "https://github.com/maykinmedia/open-inwoner"
__all__ = ("celery_app",)
