import logging
from typing import List, Optional

from django.conf import settings

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import (
    Catalogus,
    InformatieObjectType,
    ResultaatType,
)
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
    "result_types_for_case_type:{case_type_url}",
    timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
)
def fetch_result_types(case_type_url: str) -> List[ResultaatType]:
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "resultaattype",
            request_kwargs={"params": {"zaaktype": case_type_url}},
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
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
        response = client.retrieve("statustype", url=status_type_url)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    status_type = factory(StatusType, response)

    return status_type


def fetch_zaaktypes_no_cache() -> List[ZaakType]:
    """
    list case types
    """
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(client, "zaaktype")
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    zaak_types = factory(ZaakType, response)

    return zaak_types


@cache_result(
    "case_types_by_identification:{case_type_identification}",
    timeout=settings.CACHE_ZGW_CATALOGI_TIMEOUT,
)
def fetch_case_types_by_identification(
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
            "zaaktype",
            request_kwargs={"params": params},
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    zaak_types = factory(ZaakType, response)

    return zaak_types


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
        response = client.retrieve(
            "informatieobjecttype", url=information_object_type_url
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    information_object_type = factory(InformatieObjectType, response)

    return information_object_type
