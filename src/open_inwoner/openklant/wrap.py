import logging
from datetime import timedelta
from typing import List, Optional

from django.conf import settings

from open_inwoner.accounts.models import User
from open_inwoner.kvk.branches import get_kvk_branch_number
from open_inwoner.openklant.api_models import ContactMoment, KlantContactMoment
from open_inwoner.openklant.clients import build_client
from open_inwoner.openklant.models import KlantContactMomentAnswer, OpenKlantConfig
from open_inwoner.utils.time import instance_is_new

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


def get_kcm_answer_mapping(
    contactmomenten: list[ContactMoment],
    user: User,
) -> dict[str, KlantContactMomentAnswer]:
    to_create = []
    existing_kcms = set(
        KlantContactMomentAnswer.objects.filter(user=user).values_list(
            "contactmoment_url", flat=True
        )
    )
    for contactmoment in contactmomenten:
        if contactmoment.url in existing_kcms:
            continue

        to_create.append(
            KlantContactMomentAnswer(user=user, contactmoment_url=contactmoment.url)
        )

    KlantContactMomentAnswer.objects.bulk_create(to_create)

    kcm_answer_mapping = {
        kcm_answer.contactmoment_url: kcm_answer
        for kcm_answer in KlantContactMomentAnswer.objects.filter(user=user)
    }

    return kcm_answer_mapping


def contactmoment_has_new_answer(
    contactmoment: ContactMoment,
    local_kcm_mapping: Optional[dict[str, KlantContactMomentAnswer]] = None,
) -> bool:
    is_new = instance_is_new(
        contactmoment,
        "registratiedatum",
        timedelta(days=settings.CONTACTMOMENT_NEW_DAYS),
    )
    if local_kcm_mapping:
        is_seen = getattr(local_kcm_mapping.get(contactmoment.url), "is_seen", False)
    else:
        # In the detail view, this is automatically true
        is_seen = True
    return bool(contactmoment.antwoord) and is_new and not is_seen
