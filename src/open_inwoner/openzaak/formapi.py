import logging

from open_inwoner.openzaak.clients import build_client

from .api_models import OpenSubmission

logger = logging.getLogger(__name__)


def fetch_open_submissions(bsn: str) -> list[OpenSubmission]:
    client = build_client("form")

    if client is None:
        return []

    return client.fetch_open_submissions(bsn)
