import logging
from typing import List, Optional

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory

from open_inwoner.accounts.models import User
from open_inwoner.kvk.branches import get_kvk_branch_number
from open_inwoner.openklant.api_models import (
    ContactMoment,
    ContactMomentCreateData,
    Klant,
    KlantContactMoment,
    KlantContactRol,
    KlantCreateData,
    ObjectContactMoment,
)
from open_inwoner.openklant.clients import build_client
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openzaak.cases import fetch_case_by_url_no_cache
from open_inwoner.utils.api import get_paginated_results

logger = logging.getLogger(__name__)


def fetch_klantcontactmomenten(
    user_bsn: Optional[str] = None,
    user_kvk_or_rsin: Optional[str] = None,
    vestigingsnummer: Optional[str] = None,
) -> List[KlantContactMoment]:
    if not user_bsn and not user_kvk_or_rsin:
        return []

    if user_bsn:
        klanten = _fetch_klanten_for_bsn(user_bsn)
    elif user_kvk_or_rsin:
        klanten = _fetch_klanten_for_kvk_or_rsin(
            user_kvk_or_rsin, vestigingsnummer=vestigingsnummer
        )

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


def fetch_klantcontactmoment(
    kcm_uuid: str,
    user_bsn: Optional[str] = None,
    user_kvk_or_rsin: Optional[str] = None,
    vestigingsnummer: Optional[str] = None,
) -> Optional[KlantContactMoment]:

    cm_client = build_client("contactmomenten")
    k_client = build_client("klanten")
    if cm_client is None or k_client is None:
        return

    if not user_bsn and not user_kvk_or_rsin:
        return

    # use the list query because eSuite doesn't have all proper resources
    # see git history before this change for the original single resource version
    if user_bsn:
        kcms = fetch_klantcontactmomenten(user_bsn=user_bsn)
    elif user_kvk_or_rsin:
        kcms = fetch_klantcontactmomenten(
            user_kvk_or_rsin=user_kvk_or_rsin, vestigingsnummer=vestigingsnummer
        )

    kcm = None
    # try to grab the specific KCM
    for k in kcms:
        if kcm_uuid == str(k.uuid):
            kcm = k
            break

    return kcm


def _fetch_objectcontactmomenten_for_contactmoment(
    contactmoment: ContactMoment, *, client=None
) -> List[ContactMoment]:
    client = client or build_client("contactmomenten")
    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "objectcontactmoment",
            request_kwargs={"params": {"contactmoment": contactmoment.url}},
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    object_contact_momenten = factory(ObjectContactMoment, response)

    # resolve linked resources
    object_mapping = {}
    for ocm in object_contact_momenten:
        assert ocm.contactmoment == contactmoment.url
        ocm.contactmoment = contactmoment
        if ocm.object_type == "zaak":
            object_url = ocm.object
            # Avoid fetching the same object, if multiple relations wit the same object exist
            if ocm.object in object_mapping:
                ocm.object = object_mapping[object_url]
            else:
                ocm.object = fetch_case_by_url_no_cache(ocm.object)
                object_mapping[object_url] = ocm.object

    return object_contact_momenten


def fetch_objectcontactmomenten_for_object_type(
    contactmoment: ContactMoment, object_type: str
) -> List[ObjectContactMoment]:
    client = build_client("contactmomenten")

    moments = _fetch_objectcontactmomenten_for_contactmoment(
        contactmoment, client=client
    )

    # eSuite doesn't implement a `object_type` query parameter
    ret = [moment for moment in moments if moment.object_type == object_type]

    return ret


def fetch_objectcontactmoment(
    contactmoment: ContactMoment, object_type: str
) -> Optional[ObjectContactMoment]:
    ocms = fetch_objectcontactmomenten_for_object_type(contactmoment, object_type)
    if ocms:
        return ocms[0]


def _fetch_klanten_for_bsn(user_bsn: str, *, client=None) -> List[Klant]:
    client = client or build_client("klanten")
    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "klanten",
            params={"subjectNatuurlijkPersoon__inpBsn": user_bsn},
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    klanten = factory(Klant, response)

    return klanten


def _fetch_klanten_for_kvk_or_rsin(
    user_kvk_or_rsin: str, *, vestigingsnummer=None, client=None
) -> List[Klant]:
    client = client or build_client("klanten")
    if client is None:
        return []

    params = {"subjectNietNatuurlijkPersoon__innNnpId": user_kvk_or_rsin}

    if vestigingsnummer:
        params = {
            "subjectVestiging__vestigingsNummer": vestigingsnummer,
        }

    try:
        response = get_paginated_results(
            client,
            "klanten",
            params=params,
        )
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return []

    klanten = factory(Klant, response)

    return klanten


def fetch_klant(
    user_bsn: Optional[str] = None, user_kvk_or_rsin: Optional[str] = None
) -> Optional[Klant]:
    if not user_bsn and not user_kvk_or_rsin:
        return

    # this is technically a search operation and could return multiple records
    if user_bsn:
        klanten = _fetch_klanten_for_bsn(user_bsn)
    elif user_kvk_or_rsin:
        klanten = _fetch_klanten_for_kvk_or_rsin(user_kvk_or_rsin)

    if klanten:
        # let's use the first one
        return klanten[0]
    else:
        return


def _fetch_klantcontactmomenten_for_klant(
    klant: Klant, *, client=None
) -> List[KlantContactMoment]:
    client = client or build_client("contactmomenten")
    if client is None:
        return []

    try:
        response = get_paginated_results(
            client,
            "klantcontactmomenten",
            params={"klant": klant.url},
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
    if client is None:
        return

    try:
        response = client.get(url).json()
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    contact_moment = factory(ContactMoment, response)

    return contact_moment


def create_klant(data: KlantCreateData) -> Optional[Klant]:
    client = build_client("klanten")
    if client is None:
        return

    try:
        response = client.post("klanten", json=data).json()
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ValueError as e:
        # raised when 'Operation klant_create not found
        # TODO make this optional?
        return

    klant = factory(Klant, response)

    return klant


def patch_klant(klant: Klant, update_data) -> Optional[Klant]:
    client = build_client("klanten")
    if client is None:
        return

    try:
        response = client.patch(url=klant.url, json=update_data).json()
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    klant = factory(Klant, response)

    return klant


def create_contactmoment(
    data: ContactMomentCreateData,
    *,
    klant: Optional[Klant] = None,
    rol: Optional[str] = KlantContactRol.BELANGHEBBENDE
) -> Optional[ContactMoment]:
    client = build_client("contactmomenten")
    if client is None:
        return

    try:
        response = client.post("contactmomenten", json=data).json()
    except (RequestException, ClientError) as e:
        logger.exception("exception while making request", exc_info=e)
        return

    contactmoment = factory(ContactMoment, response)

    if klant:
        # relate contact to klant though a klantcontactmoment
        try:
            response = client.post(
                "klantcontactmomenten",
                json={
                    "klant": klant.url,
                    "contactmoment": contactmoment.url,
                    "rol": rol,
                },
            ).json()
        except (RequestException, ClientError) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        # build some more complete result data
        # kcm = factory(KlantContactMoment, response)
        # kcm.klant = klant
        # kcm.contactmoment = contactmoment
    #     contactmoment.klantcontactmomenten = [kcm]
    # else:
    #     contactmoment.klantcontactmomenten = []

    return contactmoment


def get_fetch_parameters(request, use_vestigingsnummer: bool = False) -> dict:
    """
    Determine the parameters used to perform Klanten/Contactmomenten fetches
    """
    user = request.user

    if user.bsn:
        return {"user_bsn": user.bsn}
    elif user.kvk:
        kvk_or_rsin = user.kvk
        config = OpenKlantConfig.get_solo()
        if config.use_rsin_for_innNnpId_query_parameter:
            kvk_or_rsin = user.rsin

        parameters = {"user_kvk_or_rsin": kvk_or_rsin}
        if use_vestigingsnummer:
            vestigingsnummer = get_kvk_branch_number(request.session)
            if vestigingsnummer:
                parameters.update({"vestigingsnummer": vestigingsnummer})
        return parameters
    return {}
