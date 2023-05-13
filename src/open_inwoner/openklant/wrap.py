import logging
from typing import List, Optional

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.service import get_paginated_results

from open_inwoner.openklant.api_models import ContactMoment, Klant, KlantContactMoment
from open_inwoner.openklant.clients import build_client

logger = logging.getLogger(__name__)


def fetch_klantcontactmomenten_for_bsn(user_bsn: str) -> List[KlantContactMoment]:
    klanten = _fetch_klanten_for_bsn(user_bsn)
    if klanten is None:
        return []

    client = build_client("contactmomenten")

    ret = list()
    for klant in klanten:
        moments = _fetch_klantcontactmomenten_for_klant(klant, client=client)
        ret.extend(moments)

    # combine sorting for moments of all klanten for a bsn
    ret.sort(key=lambda kcm: kcm.contactmoment.registratiedatum)

    return ret


def fetch_klantcontactmoment_for_bsn(
    kcm_uuid: str, user_bsn: str
) -> Optional[KlantContactMoment]:

    cm_client = build_client("contactmomenten")
    k_client = build_client("klanten")

    try:
        response = cm_client.retrieve("klantcontactmoment", uuid=kcm_uuid)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    kcm = factory(KlantContactMoment, response)

    # let's make sure our BSN has access to this
    klanten = _fetch_klanten_for_bsn(user_bsn, client=k_client)
    if not klanten:
        return

    klanten_url_map = {k.url: k for k in klanten}
    if kcm.klant not in klanten_url_map:
        # this was not a klantcontactmoment for our BSN
        return

    kcm.klant = klanten_url_map[kcm.klant]

    # resolve
    kcm.contactmoment = _fetch_contactmoment(kcm.contactmoment, client=cm_client)

    return kcm


def _fetch_klanten_for_bsn(user_bsn: str, *, client=None) -> List[Klant]:
    client = client or build_client("klanten")
    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "klant",
            request_kwargs={"params": {"subjectNatuurlijkPersoon__inpBsn": user_bsn}},
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    klanten = factory(Klant, response)

    return klanten


def _fetch_klantcontactmomenten_for_klant(
    klant: Klant, *, client=None
) -> List[KlantContactMoment]:
    client = client or build_client("contactmomenten")

    try:
        response = get_paginated_results(
            client,
            "klantcontactmoment",
            request_kwargs={"params": {"klant": klant.url}},
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    klanten_contact_moments = factory(KlantContactMoment, response)

    # resolve linked resources
    for kcm in klanten_contact_moments:
        assert kcm.klant == klant.url
        kcm.klant = klant
        kcm.contactmoment = _fetch_contactmoment(kcm.contactmoment, client=client)

    return klanten_contact_moments


def _fetch_contactmoment(url, *, client=None) -> Optional[ContactMoment]:
    client = client or build_client("contactmomenten")
    try:
        response = client.retrieve("contactmoment", url=url)
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    contact_moment = factory(ContactMoment, response)

    return contact_moment
