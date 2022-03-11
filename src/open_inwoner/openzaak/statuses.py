import logging
from typing import List

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import StatusType
from zgw_consumers.api_models.zaken import Status
from zgw_consumers.service import get_paginated_results

from .clients import build_client

logger = logging.getLogger(__name__)


def fetch_status_history(case_url: str) -> List[Status]:
    client = build_client("zaak")

    if client is None:
        return []

    try:
        response = client.list("status", request_kwargs={"params": {"zaak": case_url}})
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    statuses = factory(Status, response["results"])

    return statuses


def fetch_status_types(zaaktype: str) -> List[StatusType]:
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "statustype",
            request_kwargs={
                "params": {"zaaktype": f"{zaaktype}"},
            },
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    status_types = factory(StatusType, response)

    return status_types
