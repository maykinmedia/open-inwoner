import logging
from typing import Iterable, List

from django.db.models import Q, QuerySet

from open_inwoner.accounts.models import User
from open_inwoner.openklant.api_models import Klant, KlantContactMoment
from open_inwoner.openklant.clients import build_client
from open_inwoner.openzaak.api_models import Notification
from open_inwoner.utils.logentry import system_action as log_system_action

logger = logging.getLogger(__name__)


def handle_contactmomenten_notification(notification: Notification):
    if notification.kanaal != "contactmomenten":
        raise Exception(
            f"handler expects kanaal 'contactmomenten' but received '{notification.kanaal}'"
        )

    if notification.resource == "contactmoment" and notification.actie in [
        "update",
        "partial_update",
    ]:
        handle_contactmoment_update(notification.resource_url)
    else:
        raise NotImplementedError("programmer error in earlier resource filter")


def get_klant_data_from_contactmomenten(
    client, klantcontactmomenten: List[KlantContactMoment]
) -> Iterable[Klant]:
    if not klantcontactmomenten:
        return []

    klanten = []
    for kcm in klantcontactmomenten:
        if kcm.klant not in klanten:
            klanten.append(kcm.klant)

    klanten = map(client.retrieve_klant_by_url, klanten)

    return klanten


def get_users_for_klanten(klanten: Iterable[Klant]) -> QuerySet[User]:
    params = {"kvk__in": [], "rsin__in": [], "bsn__in": []}
    for klant in klanten:
        if klant.subject_type == "natuurlijk_persoon":
            params["bsn__in"].append(klant.subject_identificatie["inp_bsn"])
        elif klant.subject_type == "niet_natuurlijk_persoon":
            params["kvk__in"].append(klant.subject_identificatie["inn_nnp_id"])
            params["rsin__in"].append(klant.subject_identificatie["inn_nnp_id"])

    query = Q()
    for param, value in params.items():
        query |= Q(**{param: value})

    inform_users = User.objects.filter(query)

    return inform_users


def handle_contactmoment_update(contactmoment_url: str):
    klanten_client = build_client("klanten")
    contactmomenten_client = build_client("contactmomenten")

    if not klanten_client or not contactmomenten_client:
        log_system_action(
            f"could not build client for klanten or contactmomenten API, ignoring notification "
            f"for {contactmoment_url}",
            log_level=logging.INFO,
        )
        return

    contactmoment = contactmomenten_client.retrieve_contactmoment(contactmoment_url)
    klantcontactmomenten = (
        contactmomenten_client.retrieve_klantcontactmomenten_for_contactmoment(
            contactmoment
        )
    )

    log_system_action(
        f"found klantcontactmomenten for {contactmoment_url}: {klantcontactmomenten}",
        log_level=logging.INFO,
    )

    klanten = get_klant_data_from_contactmomenten(klanten_client, klantcontactmomenten)

    inform_users = get_users_for_klanten(klanten)

    log_system_action(
        f"users found linked to {contactmoment_url}: {inform_users}",
        log_level=logging.INFO,
    )

    # TODO send email #2105
    # TODO userfeed hook? #2156
