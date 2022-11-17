import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

import requests
from requests import HTTPError, RequestException, Response
from zds_client import ClientError
from zgw_consumers.api_models.base import ZGWModel, factory

from open_inwoner.openzaak.clients import build_client

logger = logging.getLogger(__name__)


@dataclass
class InformatieObject(ZGWModel):
    url: str
    identificatie: str
    bronorganisatie: str
    creatiedatum: date
    titel: str
    vertrouwelijkheidaanduiding: str
    auteur: str
    status: str
    formaat: str
    taal: str
    versie: int
    # beginRegistratie: datetime
    bestandsnaam: str
    inhoud: str
    bestandsomvang: int
    link: str
    beschrijving: str
    ontvangstdatum: str
    verzenddatum: str
    # indicatieGebruiksrecht: str
    ondertekening: dict  # {'soort': '', 'datum': None}
    integriteit: dict  # {'algoritme': '', 'waarde': '', 'datum': None}
    informatieobjecttype: str
    locked: bool
    # bestandsdelen: List[str]


@dataclass
class ZaakInformatieObject(ZGWModel):
    url: str
    informatieobject: str
    zaak: str
    # aard_relatie_weergave: str
    titel: str
    # beschrijving: str
    registratiedatum: datetime


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


def fetch_single_information_object(info_object_url: str) -> Optional[InformatieObject]:
    client = build_client("document")

    if client is None:
        return

    try:
        response = client.retrieve("enkelvoudiginformatieobject", url=info_object_url)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    info_object = factory(InformatieObject, response)

    return info_object


def fetch_single_information_object_uuid(
    info_object_uuid: str,
) -> Optional[InformatieObject]:
    client = build_client("document")

    if client is None:
        return

    try:
        response = client.retrieve("enkelvoudiginformatieobject", uuid=info_object_uuid)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    info_object = factory(InformatieObject, response)

    return info_object


def download_document(url: str, **headers) -> Optional[Response]:
    client = build_client("document")

    if client is None:
        return

    if client.auth:
        headers.update(client.auth.credentials())

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
    except HTTPError:
        return
    else:
        return res
