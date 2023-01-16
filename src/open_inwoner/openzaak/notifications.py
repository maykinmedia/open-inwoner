import logging
from typing import List, Optional

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.models import User
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.api_models import Notification, Rol, Status, Zaak
from open_inwoner.openzaak.cases import fetch_case_roles, fetch_specific_status
from open_inwoner.openzaak.catalog import (
    fetch_single_case_type,
    fetch_single_status_type,
)
from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.exceptions import NotificationNotAcceptable
from open_inwoner.openzaak.models import UserCaseStatusNotification
from open_inwoner.openzaak.utils import is_object_visible

logger = logging.getLogger(__name__)


def handle_zaken_notification(notification: Notification):
    if notification.kanaal != "zaken":
        raise NotificationNotAcceptable(f"kanaal '{notification.kanaal}' not accepted")

    """
    - Bij een zaak-wijziging wordt gekeken of het gaat om een zaak waarvan de (mede)initiator bekend is in OIP op basis van de BSN en een actief OIP account heeft waarbij het emailadres is ingevuld. Zo niet, dan kan de notificatie genegeerd worden.
    - Gecontroleerd moet worden of het gaat om een zaak met een zaaktype die toegankelijk is vanuit OIP (controle vertrouwelijkheidsaanduiding).
    - Daarna wordt gekeken naar of de zaak een nieuwe status heeft gekregen. Zo niet, dan kan de notificatie genegeerd worden.
    - Bij een nieuwe status van een zaak wordt de statustype opgehaald vanuit de Catalogi API (  https://test.openzaak.nl/catalogi/api/v1/schema/#operation/statustype_read ). De gemeente stelt via de Catalogi API in of het wenselijk is om de initiator te informeren
    - Als ‘informeren’ op de statustype op true staat dan zijn aan de voorwaarden voldaan: de inwoner krijgt een bericht op basis van een OIP mailsjabloon (door de gemeente zelf te beheren) van de statuswijziging. De gemeente kan dan aangeven of/hoeveel informatie ze in de mailnotificatie willen opnemen.
    """

    # TODO swap logger for TimelineLog

    # on the 'zaken' channel the hoofd_object is always the zaak
    case_url = notification.hoofd_object

    # were only interested in status updates
    if notification.resource != "status":
        logger.debug(
            f"ignored notification: resource is not 'status' but '{notification.resource}' for case {case_url}"
        )
        return

    status_url = notification.resource_url

    # check if we have users that need to be informed about this case
    roles = fetch_case_roles(case_url)
    if not roles:
        logger.error(f"cannot retrieve rollen for case {case_url}")
        return

    inform_users = get_emailable_initiator_users_from_roles(roles)
    if not inform_users:
        logger.info(
            f"ignored notification: no users with bsn and valid email for as (mede)initiators in case {case_url}"
        )
        return

    # check if this is a status we want to inform on
    status = fetch_specific_status(status_url)
    if not status:
        logger.error(f"cannot retrieve status {status_url} for case {case_url}")
        return

    status_type = fetch_single_status_type(status.statustype)
    # TODO support non eSuite options
    if not status_type.informeren:
        logger.info(
            f"ignored notification: status_type.informeren is false for status {status.url} and case {case_url}"
        )
        return

    status.statustype = status_type

    # check if this case is visible
    case = fetch_case_by_url_no_cache(case_url)
    if not case:
        logger.error(f"cannot retrieve case {case_url}")
        return

    case_type = fetch_single_case_type(case.zaaktype)
    if not case_type:
        logger.error(f"cannot retrieve case_type {case.zaaktype} for case {case_url}")
        return

    case.zaaktype = case_type

    config = SiteConfiguration.get_solo()
    # TODO check if we don't want is_zaak_visible() to also check for intern/extern
    if not is_object_visible(case, config.zaak_max_confidentiality):
        logger.info(
            f"ignored notification: bad confidentiality {case.vertrouwelijkheidaanduiding} for case {case_url}"
        )
        return

    # reaching here means we're going to inform users
    logger.info(
        f"accepted notification: informing users {', '.join(map(str, inform_users))} for case {case_url}"
    )

    for user in inform_users:
        handle_status_update(user, case, status)


def handle_status_update(user: User, case: Zaak, status: Status):
    note = UserCaseStatusNotification.objects.record_if_unique_notification(
        user, case.uuid, status.uuid
    )
    if not note:
        # multiple delivery
        return

    print("sending notification informer!")
    send_status_update_email(user, case, status)


def send_status_update_email(user: User, case: Zaak, status: Status):
    """
    send the actual mail
    """
    pass


def fetch_case_by_url_no_cache(case_url: str) -> Optional[Zaak]:
    # TODO decide how this interacts with the cache
    client = build_client("zaak")
    try:
        response = client.retrieve("zaak", url=case_url)
    except RequestException as e:
        logger.exception("exception while making request", exc_info=e)
        return
    except ClientError as e:
        logger.exception("exception while making request", exc_info=e)
        return

    case = factory(Zaak, response)

    return case


def get_np_initiator_bsns_from_roles(roles: List[Rol]) -> List[str]:
    """
    iterate over Rollen and for all natural-person initiators return their BSN
    """
    ret = set()

    for role in roles:
        if role.omschrijving_generiek not in (
            RolOmschrijving.initiator,
            RolOmschrijving.medeinitiator,
        ):
            continue
        if role.betrokkene_type != RolTypes.natuurlijk_persoon:
            continue
        if not role.betrokkene_identificatie:
            continue
        bsn = role.betrokkene_identificatie.get("inp_bsn")
        if not bsn:
            continue
        ret.add(bsn)

    return list(ret)


def get_emailable_initiator_users_from_roles(roles: List[Rol]) -> List[User]:
    """
    iterate over Rollen and return User objects for all natural-person initiators we can notify
    """
    bsn_list = get_np_initiator_bsns_from_roles(roles)
    if not bsn_list:
        return []
    users = list(
        User.objects.filter(bsn__in=bsn_list, is_active=True).having_usable_email()
    )
    return users
