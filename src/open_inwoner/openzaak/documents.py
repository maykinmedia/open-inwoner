from open_inwoner.openzaak.api_models import InformatieObject
from open_inwoner.openzaak.clients import DocumentenClient
from open_inwoner.openzaak.utils import zgw_zaken_cache


@zgw_zaken_cache("information_object_url:{url}")
def fetch_single_information_object_from_url(
    url: str, api_group
) -> InformatieObject | None:
    return api_group.documenten_client._fetch_single_information_object(url=url)


# not cached because currently only used in info-object download view
def fetch_single_information_object_uuid(
    uuid: str, documenten_client: DocumentenClient
) -> InformatieObject | None:
    return documenten_client._fetch_single_information_object(uuid=uuid)
