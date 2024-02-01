import logging
from typing import List, Optional

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

logger = logging.getLogger(__name__)


def fetch_klantcontactmomenten(
    user_bsn: Optional[str] = None,
    user_kvk_or_rsin: Optional[str] = None,
    vestigingsnummer: Optional[str] = None,
) -> List[KlantContactMoment]:
    if not user_bsn and not user_kvk_or_rsin:
        return []

    client = build_client("klanten")
    if client is None:
        return []

    if user_bsn:
        klanten = client.retrieve_klanten_for_bsn(user_bsn)
    elif user_kvk_or_rsin:
        klanten = client.retrieve_klanten_for_kvk_or_rsin(
            user_kvk_or_rsin, vestigingsnummer=vestigingsnummer
        )

    if klanten is None:
        return []

    client = build_client("contactmomenten")
    if client is None:
        return []

    ret = list()
    for klant in klanten:
        moments = client.retrieve_klantcontactmomenten_for_klant(klant)
        ret.extend(moments)

    # combine sorting for moments of all klanten for a bsn
    ret.sort(key=lambda kcm: kcm.contactmoment.registratiedatum, reverse=True)

    return ret


def fetch_klantcontactmoment(
    kcm_uuid: str,
    user_bsn: Optional[str] = None,
    user_kvk_or_rsin: Optional[str] = None,
    vestigingsnummer: Optional[str] = None,
) -> Optional[KlantContactMoment]:
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


def fetch_objectcontactmoment(
    contactmoment: ContactMoment, object_type: str
) -> Optional[ObjectContactMoment]:
    client = build_client("contactmomenten")
    if client is None:
        return

    return client.retrieve_objectcontactmoment(contactmoment, object_type)


def fetch_klant(
    user_bsn: Optional[str] = None,
    user_kvk_or_rsin: Optional[str] = None,
    client=None,
) -> Optional[Klant]:
    client = client or build_client("klanten")
    if client is None:
        return

    return client.retrieve_klant(user_bsn=user_bsn, user_kvk_or_rsin=user_kvk_or_rsin)


def create_klant(data: KlantCreateData) -> Optional[Klant]:
    client = build_client("klanten")
    if client is None:
        return

    return client.create_klant(data)


def patch_klant(klant: Klant, update_data) -> Optional[Klant]:
    client = build_client("klanten")
    if client is None:
        return

    return client.partial_update_klant(klant, update_data)


def create_contactmoment(
    data: ContactMomentCreateData,
    *,
    klant: Optional[Klant] = None,
    rol: Optional[str] = KlantContactRol.BELANGHEBBENDE
) -> Optional[ContactMoment]:
    client = build_client("contactmomenten")
    if client is None:
        return

    return client.create_contactmoment(data, klant=klant, rol=rol)


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
