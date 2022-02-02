import logging

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import StatusType
from zgw_consumers.api_models.zaken import Status
from zgw_consumers.concurrent import parallel

from .clients import build_client

logger = logging.getLogger(__name__)


def fetch_status_history(user, case_url):
    client = build_client("zaak")

    if client is None or user.bsn is None:
        return []

    try:
        response = client.list("status", request_kwargs={"params": {"zaak": case_url}})
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    status_list = [factory(Status, status) for status in response.get("results", [])]

    return status_list


def fetch_status_type(user, status_type_urls):
    client = build_client("catalogi")

    if client is None or user.bsn is None:
        return []

    with parallel() as executor:
        try:
            _status_type_list = executor.map(
                lambda url: client.retrieve("statustypen", url=url),
                status_type_urls,
            )
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return []

    status_type_list = factory(StatusType, list(_status_type_list))

    return status_type_list
