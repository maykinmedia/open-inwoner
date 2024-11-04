import logging

from django.conf import settings

from open_inwoner.openzaak.api_models import InformatieObject
from open_inwoner.openzaak.clients import DocumentenClient

from ..utils.decorators import cache as cache_result

logger = logging.getLogger(__name__)


@cache_result("information_object_url:{url}", timeout=settings.CACHE_ZGW_ZAKEN_TIMEOUT)
def fetch_single_information_object_from_url(
    url: str, api_group
) -> InformatieObject | None:
    return api_group.documenten_client._fetch_single_information_object(url=url)


# not cached because currently only used in info-object download view
def fetch_single_information_object_uuid(
    uuid: str, documenten_client: DocumentenClient
) -> InformatieObject | None:
    return documenten_client._fetch_single_information_object(uuid=uuid)
