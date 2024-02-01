import logging
from typing import List, Optional

from django.conf import settings

from zgw_consumers.api_models.catalogi import Catalogus

from ..utils.decorators import cache as cache_result
from .api_models import InformatieObjectType, ResultaatType, StatusType, ZaakType
from .clients import build_client

logger = logging.getLogger(__name__)


# not cached because only used by tools,
# and because caching (stale) listings can break lookups
def fetch_status_types_no_cache(case_type_url: str) -> List[StatusType]:
    client = build_client("catalogi")

    if client is None:
        return []

    return client.fetch_status_types_no_cache(case_type_url)


# not cached because only used by tools,
# and because caching (stale) listings can break lookups
def fetch_result_types_no_cache(case_type_url: str) -> List[ResultaatType]:
    client = build_client("catalogi")

    if client is None:
        return []

    return client.fetch_result_types_no_cache(case_type_url)


def fetch_single_status_type(status_type_url: str) -> Optional[StatusType]:
    client = build_client("catalogi")

    if client is None:
        return

    return client.fetch_single_status_type(status_type_url)


def fetch_single_resultaat_type(resultaat_type_url: str) -> Optional[ResultaatType]:
    client = build_client("catalogi")

    if client is None:
        return

    return client.fetch_single_resultaat_type(resultaat_type_url)


def fetch_zaaktypes_no_cache() -> List[ZaakType]:
    """
    list case types
    """
    client = build_client("catalogi")

    if client is None:
        return []

    return client.fetch_zaaktypes_no_cache()


# not cached because only used by cronjob
# and because caching (stale) listings can break lookups
def fetch_case_types_by_identification_no_cache(
    case_type_identification: str, catalog_url: Optional[str] = None
) -> List[ZaakType]:
    client = build_client("catalogi")

    if client is None:
        return []

    return client.fetch_case_types_by_identification_no_cache(
        case_type_identification, catalog_url=catalog_url
    )


def fetch_single_case_type(case_type_url: str) -> Optional[ZaakType]:
    client = build_client("catalogi")

    if client is None:
        return

    return client.fetch_single_case_type(case_type_url)


def fetch_catalogs_no_cache() -> List[Catalogus]:
    """
    note the eSuite implementation returns status 500 for this call
    """
    client = build_client("catalogi")

    if client is None:
        return []

    return client.fetch_catalogs_no_cache()


def fetch_single_information_object_type(
    information_object_type_url: str,
) -> Optional[InformatieObjectType]:
    client = build_client("catalogi")

    if client is None:
        return

    return client.fetch_single_information_object_type(information_object_type_url)
