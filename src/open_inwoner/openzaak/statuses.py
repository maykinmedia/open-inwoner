import logging
from typing import List, Optional

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import StatusType
from zgw_consumers.api_models.zaken import ZGWModel, Status
from zgw_consumers.concurrent import parallel
from zgw_consumers.service import get_paginated_results

from .clients import build_client

logger = logging.getLogger(__name__)

### Workaround for Groningen e-Suite #773 ###

from dataclasses import dataclass
from datetime import date, datetime

@dataclass
class ZaakInformatieObject(ZGWModel):
    url: str
    informatieobject: str
    zaak: str
    # aard_relatie_weergave: str
    titel: str
    # beschrijving: str
    registratiedatum: datetime

### ###


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


def fetch_specific_statuses(status_urls: List[str]) -> List[Status]:
    client = build_client("zaak")

    if client is None:
        return []
    status_urls = [u.replace("dacceptatiemidoffice", "service-tst.gateway") for u in status_urls]
    with parallel() as executor:
        _statuses = executor.map(
            lambda url: client.retrieve("status", url=url),
            status_urls,
        )

    statuses = factory(Status, list(_statuses))

    return statuses


def fetch_status_types(case_type=None) -> List[StatusType]:
    client = build_client("catalogi")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "statustype",
            request_kwargs={
                "params": {"zaaktype": case_type},
            }
            if case_type
            else None,
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    status_types = factory(StatusType, response)

    return status_types


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


def fetch_case_information_objects(case_url: str) -> List[ZaakInformatieObject]:
    client = build_client("zaak")

    if client is None:
        return []

    try:
        response = client.list(
            "zaakinformatieobject",
            request_kwargs={
                "params": {"zaak": case_url},
            },
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    case_info_objects = factory(ZaakInformatieObject, response)

    return case_info_objects
