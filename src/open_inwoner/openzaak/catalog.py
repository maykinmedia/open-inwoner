import logging
from typing import List, Optional

from django.conf import settings

from requests import RequestException
from zds_client import ClientError, get_operation_url
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus
from zgw_consumers.service import get_paginated_results

from .api_models import StatusType, ZaakType
from .clients import build_client
from .utils import cache as cache_result, get_retrieve_resource_by_uuid_url

logger = logging.getLogger(__name__)


@cache_result(
    "status_types_for_case_type:{case_type_url}",
    timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
)
def fetch_status_types(case_type_url: str) -> List[StatusType]:
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "statustype",
            request_kwargs={"params": {"zaaktype": case_type_url}},
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    status_types = factory(StatusType, response)

    return status_types


@cache_result(
    "status_type:{status_type_url}", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT
)
def fetch_single_status_type(status_type_url: str) -> Optional[StatusType]:
    client = build_client("catalogi")

    if client is None:
        return

    try:
        response = client.retrieve("statustype", url=status_type_url)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    status_type = factory(StatusType, response)

    return status_type


@cache_result("case_types:{catalog_url}", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT)
def fetch_catalog_zaaktypes(catalog_url: str) -> List[ZaakType]:
    """
    list case types from catalog
    """
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "zaaktype",
            request_kwargs={"params": {"catalogus": catalog_url}},
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    zaak_types = factory(ZaakType, response)

    return zaak_types


# implicitly uses cached data
def fetch_catalog_case_type_by_identification(
    catalog_url: str, case_type_identification: str
) -> List[ZaakType]:
    """
    list case types from a catalogue for a given 'identificatie' field
    """
    # re-use cached list
    zaak_types = fetch_catalog_zaaktypes(catalog_url)

    ret = list()
    for zt in zaak_types:
        if zt.identificatie == case_type_identification:
            ret.append(zt)
    return ret


def fetch_single_case_type_uuid(uuid: str) -> Optional[ZaakType]:
    """
    this is suboptimal until we upgrade the client/cache situation
    """
    client = build_client("catalogi")

    if client is None:
        return None

    # make url to use same cache
    url = get_retrieve_resource_by_uuid_url(client, "zaaktype", uuid)
    return fetch_single_case_type(url)


@cache_result("case_type:{case_type_url}", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT)
def fetch_single_case_type(case_type_url: str) -> Optional[ZaakType]:
    client = build_client("catalogi")

    if client is None:
        return

    try:
        response = client.retrieve("zaaktype", url=case_type_url)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case_type = factory(ZaakType, response)

    return case_type


@cache_result("catalogs", timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT)
def fetch_catalogs() -> List[Catalogus]:
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "catalogus",
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    catalogs = factory(Catalogus, response)

    return catalogs
