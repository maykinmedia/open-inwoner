from datetime import timedelta
from typing import NotRequired, TypedDict

from django.conf import settings

from open_inwoner.accounts.models import User
from open_inwoner.openklant.api_models import ContactMoment
from open_inwoner.openklant.models import KlantContactMomentAnswer
from open_inwoner.utils.time import instance_is_new


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
