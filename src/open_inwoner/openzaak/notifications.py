import logging
from typing import List

from django.urls import reverse

from mail_editor.helpers import find_template
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import Notification, Rol, Status, Zaak
from open_inwoner.openzaak.cases import (
    fetch_case_by_url_no_cache,
    fetch_case_roles,
    fetch_specific_status,
    fetch_status_history_no_cache,
)
from open_inwoner.openzaak.catalog import (
    fetch_single_case_type,
    fetch_single_status_type,
)
from open_inwoner.openzaak.models import OpenZaakConfig, UserCaseStatusNotification
from open_inwoner.openzaak.utils import get_zaak_type_config, is_zaak_visible
from open_inwoner.utils.logentry import system_action as log_system_action
from open_inwoner.utils.url import build_absolute_url

logger = logging.getLogger(__name__)


def handle_zaken_notification(notification: Notification):
    if notification.kanaal != "zaken":
        raise Exception(
            f"handler expects kanaal 'zaken' but received '{notification.kanaal}'"
        )

    # on the 'zaken' channel the hoofd_object is always the zaak
    case_url = notification.hoofd_object

    oz_config = OpenZaakConfig.get_solo()

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

    status_history = fetch_status_history_no_cache(case_url)
    if not status_history:
        log_system_action(
            f"ignored notification: cannot retrieve status_history for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    if len(status_history) == 1:
        log_system_action(
            f"ignored notification: skip initial status notification for case {case_url}",
            log_level=logging.INFO,
        )
        return

    for s in status_history:
        if s.url == status_url:
            status = s
            break
    else:
        status = fetch_specific_status(status_url)

    if not status:
        log_system_action(
            f"ignored notification: cannot retrieve status {status_url} for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    status_type = fetch_single_status_type(status.statustype)
    if not status_type:
        log_system_action(
            f"ignored notification: cannot retrieve status_type {status.statustype} for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    if not oz_config.skip_notification_statustype_informeren:
        if not status_type.informeren:
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

    # check the ZaakTypeConfig
    if oz_config.skip_notification_statustype_informeren:
        ztc = get_zaak_type_config(case_type)
        if not ztc:
            log_system_action(
                f"ignored notification: 'skip_notification_statustype_informeren' is True but cannot retrieve case_type configuration '{case.zaaktype.identificatie}' for case {case_url}",
                log_level=logging.INFO,
            )
            return
        elif not ztc.notify_status_changes:
            log_system_action(
                f"ignored notification: case_type configuration '{case.zaaktype.identificatie}' found but 'notify_status_changes' is False for case {case_url}",
                log_level=logging.INFO,
            )
            return

    if not is_zaak_visible(case):
        log_system_action(
            f"ignored notification: case not visible after applying website visibility filter for case {case_url}",
            log_level=logging.INFO,
        )
        return

    # reaching here means we're going to inform users
    log_system_action(
        f"accepted notification: attempt informing users {', '.join(sorted(map(str, inform_users)))} for case {case_url}",
        log_level=logging.INFO,
    )
    for user in inform_users:
        # TODO run in try/except so it can't bail?
        handle_status_update(user, case, status)


def handle_status_update(user: User, case: Zaak, status: Status):
    note = UserCaseStatusNotification.objects.record_if_unique_notification(
        user, case.uuid, status.uuid
    )
    if not note:
        log_system_action(
            f"ignored duplicate notification delivery for user '{user}' status {status.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    send_status_update_email(user, case, status)

    log_system_action(
        f"send notification email for user '{user}' status {status.url} case {case.url}",
        log_level=logging.INFO,
    )


def send_status_update_email(user: User, case: Zaak, status: Status):
    """
    send the actual mail
    """
    case_detail_url = build_absolute_url(
        reverse("accounts:case_status", kwargs={"object_id": str(case.uuid)})
    )

    template = find_template("case_notification")
    context = {
        "identification": case.identificatie,
        "type_description": case.zaaktype.omschrijving,
        "start_date": case.startdatum,
        "case_link": case_detail_url,
    }
    template.send_email([user.email], context)


# - - - - -


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
