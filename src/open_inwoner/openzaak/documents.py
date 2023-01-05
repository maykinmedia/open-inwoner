import logging
from typing import Optional

from django.conf import settings

from requests import HTTPError, RequestException, Response
from zds_client import ClientError
from zgw_consumers.api_models.base import factory

from open_inwoner.openzaak.api_models import InformatieObject

from .baseclient import BaseClient
from .utils import cache as cache_result

logger = logging.getLogger(__name__)


@cache_result("information_object_url:{url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_single_information_object_url(
    client: BaseClient, url: str
) -> Optional[InformatieObject]:
    return _fetch_single_information_object(client, url=url)


# not cached because currently only used in info-object download view
def fetch_single_information_object_uuid(
    client: BaseClient, uuid: str
) -> Optional[InformatieObject]:
    return _fetch_single_information_object(client, uuid=uuid)


def _fetch_single_information_object(
    client: BaseClient, *, url: Optional[str] = None, uuid: Optional[str] = None
) -> Optional[InformatieObject]:
    if (url and uuid) or (not url and not uuid):
        raise ValueError("supply either 'url' or 'uuid' argument")
    if not client.service:
        return

    try:
        if url:
            response = client.api.retrieve("enkelvoudiginformatieobject", url=url)
        else:
            response = client.api.retrieve("enkelvoudiginformatieobject", uuid=uuid)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    info_object = factory(InformatieObject, response)

    return info_object


def download_document(client: BaseClient, url: str) -> Optional[Response]:
    if not client.service:
        return

    try:
        res = client.session.get(url)
        res.raise_for_status()
    except HTTPError as e:
        logger.exception("exception while making request", exc_info=e)
    else:
        return res
