import logging
from typing import List, Optional

from requests import RequestException
from zds_client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import Notification, Rol, Status, Zaak
from open_inwoner.openzaak.cases import fetch_case_roles, fetch_specific_status
from open_inwoner.openzaak.catalog import (
    fetch_single_case_type,
    fetch_single_status_type,
)
from open_inwoner.openzaak.clients import build_client
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.utils import is_object_visible
from open_inwoner.utils.logentry import system_action as log_system_action

logger = logging.getLogger(__name__)


def handle_zaken_notification(notification: Notification):
    if notification.kanaal != "zaken":
        raise Exception(
            f"handler expects kanaal 'zaken' but received '{notification.kanaal}'"
        )

    # on the 'zaken' channel the hoofd_object is always the zaak
    case_url = notification.hoofd_object

    # were only interested in status updates
    if notification.resource != "status":
        log_system_action(
            f"ignored notification: resource is not 'status' but '{notification.resource}' for case {case_url}",
            log_level=logging.INFO,
        )
        return

    status_url = notification.resource_url

    # check if we have users that need to be informed about this case
    roles = fetch_case_roles(case_url)
    if not roles:
        log_system_action(
            f"ignored notification: cannot retrieve rollen for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    inform_users = get_emailable_initiator_users_from_roles(roles)
    if not inform_users:
        log_system_action(
            f"ignored notification: no users with bsn and valid email as (mede)initiators in case {case_url}",
            log_level=logging.INFO,
        )
        return

    # check if this is a status we want to inform on
    status = fetch_specific_status(status_url)
    if not status:
        log_system_action(
            f"ignored notification: cannot retrieve status {status_url} for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    status_type = fetch_single_status_type(status.statustype)
    # TODO support non eSuite options
    if not status_type:
        log_system_action(
            f"ignored notification: cannot retrieve status_type {status.statustype} for case {case_url}",
            log_level=logging.ERROR,
        )
        return
    elif not status_type.informeren:
        log_system_action(
            f"ignored notification: status_type.informeren is false for status {status.url} and case {case_url}",
            log_level=logging.INFO,
        )
        return

    status.statustype = status_type

    # check if this case is visible
    case = fetch_case_by_url_no_cache(case_url)
    if not case:
        log_system_action(
            f"ignored notification: cannot retrieve case {case_url}",
            log_level=logging.ERROR,
        )
        return

    case_type = fetch_single_case_type(case.zaaktype)
    if not case_type:
        log_system_action(
            f"ignored notification: cannot retrieve case_type {case.zaaktype} for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    case.zaaktype = case_type

    config = OpenZaakConfig.get_solo()
    # TODO check if we don't want is_zaak_visible() to also check for intern/extern
    if not is_object_visible(case, config.zaak_max_confidentiality):
        log_system_action(
            f"ignored notification: bad confidentiality '{case.vertrouwelijkheidaanduiding}' for case {case_url}",
            log_level=logging.INFO,
        )
        return

    # reaching here means we're going to inform users
    log_system_action(
        f"accepted notification: informing users {', '.join(sorted(map(str, inform_users)))} for case {case_url}",
        log_level=logging.INFO,
    )
    for user in inform_users:
        # TODO run in try/except so it can't bail?
        handle_status_update(user, case, status)


def handle_status_update(user: User, case: Zaak, status: Status):
    logger.debug("sending notification informer!")
    # TODO still need to de-duplicate
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
