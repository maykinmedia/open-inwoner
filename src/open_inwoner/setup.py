"""
Bootstrap the environment.

Load the secrets from the .env file and store them in the environment, so
they are available for Django settings initialization.

.. warning::

    do NOT import anything Django related here, as this file needs to be loaded
    before Django is initialized.
"""
import logging
import os

from django.conf import settings

from dotenv import load_dotenv
from requests import Session

logger = logging.getLogger(__name__)


def setup_env():
    # load the environment variables containing the secrets/config
    dotenv_path = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, ".env")
    load_dotenv(dotenv_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "open_inwoner.conf.dev")

    monkeypatch_requests()


def monkeypatch_requests():
    """
    Add a default timeout for any requests calls.
    """
    if hasattr(Session, "_original_request"):
        logger.debug(
            "Session is already patched OR has an ``_original_request`` attribute."
        )
        return

    Session._original_request = Session.request

    def new_request(self, *args, **kwargs):
        kwargs.setdefault("timeout", settings.DEFAULT_TIMEOUT_REQUESTS)
        return self._original_request(*args, **kwargs)

    Session.request = new_request
