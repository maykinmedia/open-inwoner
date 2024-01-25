import logging
from typing import List, Optional

from django.conf import settings

from requests import RequestException
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus

from open_inwoner.utils.api import ClientError, get_paginated_results

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

    try:
        response = get_paginated_results(
            client,
            "statustypen",
            params={"zaaktype": case_type_url},
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    status_types = factory(StatusType, response)

    return status_types


# not cached because only used by tools,
# and because caching (stale) listings can break lookups
def fetch_result_types_no_cache(case_type_url: str) -> List[ResultaatType]:
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "resultaattypen",
            params={"zaaktype": case_type_url},
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    result_types = factory(ResultaatType, response)

    return result_types


@cache_result(
    "status_type:{status_type_url}", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT
)
def fetch_single_status_type(status_type_url: str) -> Optional[StatusType]:
    client = build_client("catalogi")

    if client is None:
        return

    try:
        response = client.get(url=status_type_url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    status_type = factory(StatusType, response)

    return status_type


@cache_result(
    "resultaat_type:{resultaat_type_url}", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT
)
def fetch_single_resultaat_type(resultaat_type_url: str) -> Optional[ResultaatType]:
    client = build_client("catalogi")

    if client is None:
        return

    try:
        response = client.get(url=resultaat_type_url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    resultaat_type = factory(ResultaatType, response)

    return resultaat_type


# not cached because only used by tools,
# and because caching (stale) listings can break lookups
def fetch_zaaktypes_no_cache() -> List[ZaakType]:
    """
    list case types
    """
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(client, "zaaktypen")
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    zaak_types = factory(ZaakType, response)

    return zaak_types


# not cached because only used by cronjob
# and because caching (stale) listings can break lookups
def fetch_case_types_by_identification_no_cache(
    case_type_identification: str, catalog_url: Optional[str] = None
) -> List[ZaakType]:
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        params = {
            "identificatie": case_type_identification,
        }
        if catalog_url:
            params["catalogus"] = catalog_url

        response = get_paginated_results(
            client,
            "zaaktypen",
            params=params,
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    zaak_types = factory(ZaakType, response)

    return zaak_types


# cached implicitly by fetch_single_case_type()
def fetch_single_case_type_uuid(uuid: str) -> Optional[ZaakType]:
    """
    this is suboptimal until we upgrade the client/cache situation
    """
    client = build_client("catalogi")

    if client is None:
        return None

    # make url to use same cache
    return fetch_single_case_type(f"zaaktypen/{uuid}")


@cache_result("case_type:{case_type_url}", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT)
def fetch_single_case_type(case_type_url: str) -> Optional[ZaakType]:
    client = build_client("catalogi")

    if client is None:
        return

    try:
        response = client.get(url=case_type_url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case_type = factory(ZaakType, response)

    return case_type


def fetch_catalogs_no_cache() -> List[Catalogus]:
    """
    note the eSuite implementation returns status 500 for this call
    """
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "catalogussen",
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    catalogs = factory(Catalogus, response)

    return catalogs


@cache_result(
    "information_object_type:{information_object_type_url}",
    timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
)
def fetch_single_information_object_type(
    information_object_type_url: str,
) -> Optional[InformatieObjectType]:
    client = build_client("catalogi")

    if client is None:
        return

    try:
        response = client.get(url=information_object_type_url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    information_object_type = factory(InformatieObjectType, response)

    return information_object_type
