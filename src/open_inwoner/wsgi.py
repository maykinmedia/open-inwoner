"""
WSGI config for open_inwoner project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""
from django.core.wsgi import get_wsgi_application

from open_inwoner.setup import setup_env

setup_env()

application = get_wsgi_application()
