import logging
from typing import Optional

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.functional import SimpleLazyObject

from requests import Response
from zgw_consumers.client import build_client

from open_inwoner.openzaak.api_models import InformatieObject
from open_inwoner.openzaak.clients import build_client

from ..utils.decorators import cache as cache_result

logger = logging.getLogger(__name__)


@cache_result("information_object_url:{url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_single_information_object_url(url: str) -> Optional[InformatieObject]:
    return _fetch_single_information_object(url=url)


# not cached because currently only used in info-object download view
def fetch_single_information_object_uuid(uuid: str) -> Optional[InformatieObject]:
    return _fetch_single_information_object(uuid=uuid)


def _fetch_single_information_object(
    *, url: Optional[str] = None, uuid: Optional[str] = None
) -> Optional[InformatieObject]:
    client = build_client("document")

    if client is None:
        return

    return client._fetch_single_information_object(url=url, uuid=uuid)


def download_document(url: str) -> Optional[Response]:
    client = build_client("document")
    if client is None:
        return

    return client.download_document(url)


def upload_document(
    user: SimpleLazyObject,
    file: InMemoryUploadedFile,
    title: str,
    informatieobjecttype_url: str,
    source_organization: str,
) -> Optional[dict]:

    client = build_client("document")
    if client is None:
        return

    return client.upload_document(
        user, file, title, informatieobjecttype_url, source_organization
    )
