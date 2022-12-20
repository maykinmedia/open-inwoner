import logging
from typing import List, Optional

from django.conf import settings

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import StatusType
from zgw_consumers.service import get_paginated_results

from .api_models import ZaakType
from .clients import build_client
from .utils import cache as cache_result

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
