from datetime import timedelta
from typing import NotRequired, TypedDict

from django.conf import settings

from open_inwoner.accounts.models import User
from open_inwoner.openklant.api_models import ContactMoment, KlantContactMoment
from open_inwoner.openklant.clients import (
    build_contactmomenten_client,
    build_klanten_client,
)
from open_inwoner.openklant.models import KlantContactMomentAnswer
from open_inwoner.utils.time import instance_is_new


def fetch_klantcontactmomenten(
    user_bsn: str | None = None,
    user_kvk_or_rsin: str | None = None,
    vestigingsnummer: str | None = None,
) -> list[KlantContactMoment]:
    if not user_bsn and not user_kvk_or_rsin:
        return []

    client = build_klanten_client()
    if client is None:
        return []

    if user_bsn:
        klanten = client.retrieve_klanten_for_bsn(user_bsn)
    elif user_kvk_or_rsin:
        klanten = client.retrieve_klanten_for_kvk_or_rsin(
            user_kvk_or_rsin, vestigingsnummer=vestigingsnummer
        )

    client = build_contactmomenten_client()
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
    user_bsn: str | None = None,
    user_kvk_or_rsin: str | None = None,
    vestigingsnummer: str | None = None,
) -> KlantContactMoment | None:
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


class BsnFetchParam(TypedDict):
    user_bsn: str


class OrgFetchParam(TypedDict):
    user_kvk_or_rsin: str
    vestigingsnummer: NotRequired[str]


FetchParameters = BsnFetchParam | OrgFetchParam


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
    local_kcm_mapping: dict[str, KlantContactMomentAnswer] | None = None,
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
