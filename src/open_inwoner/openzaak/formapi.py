import logging

from open_inwoner.openzaak.clients import build_forms_client

from .api_models import OpenSubmission

logger = logging.getLogger(__name__)


def fetch_open_submissions(bsn: str) -> list[OpenSubmission]:
    client = build_forms_client()

    if client is None:
        return []

    return client.fetch_open_submissions(bsn)
