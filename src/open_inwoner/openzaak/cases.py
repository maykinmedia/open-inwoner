import logging
from typing import List, Optional

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.zaken import Status, Zaak
from zgw_consumers.service import get_paginated_results

from .api_models import Zaak, ZaakInformatieObject
from .clients import build_client

logger = logging.getLogger(__name__)


def fetch_cases(user_bsn: str) -> List[Zaak]:
    client = build_client("zaak")

    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "zaak",
            request_kwargs={
                "params": {
                    "rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": user_bsn
                },
            },
        )
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return []
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    cases = factory(Zaak, response)

    return cases


def fetch_single_case(case_uuid: str) -> Optional[Zaak]:
    client = build_client("zaak")

    if client is None:
        return

    try:
        response = client.retrieve("zaak", uuid=case_uuid)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case = factory(Zaak, response)

    return case


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

    _statuses = []
    for url in status_urls:
        _statuses += [client.retrieve("status", url=url)]

    statuses = factory(Status, list(_statuses))

    return statuses
