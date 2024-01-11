import logging
from datetime import timedelta
from typing import List

from django.conf import settings
from django.urls import reverse

from mail_editor.helpers import find_template
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import (
    Notification,
    Rol,
    Status,
    Zaak,
    ZaakInformatieObject,
)
from open_inwoner.openzaak.cases import (
    fetch_case_by_url_no_cache,
    fetch_case_roles,
    fetch_single_case_information_object,
    fetch_single_status,
    fetch_status_history_no_cache,
    resolve_status,
)
from open_inwoner.openzaak.catalog import (
    fetch_single_case_type,
    fetch_single_status_type,
)
from open_inwoner.openzaak.documents import fetch_single_information_object_url
from open_inwoner.openzaak.managers import UserCaseInfoObjectNotificationManager
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    UserCaseInfoObjectNotification,
    UserCaseStatusNotification,
)
from open_inwoner.openzaak.utils import (
    get_zaak_type_config,
    get_zaak_type_info_object_type_config,
    is_info_object_visible,
    is_zaak_visible,
)
from open_inwoner.userfeed import hooks
from open_inwoner.utils.logentry import system_action as log_system_action
from open_inwoner.utils.url import build_absolute_url

from .models import ZaakTypeStatusTypeConfig

logger = logging.getLogger(__name__)


def wrap_join(iter, glue="") -> str:
    parts = list(sorted(f"'{v}'" for v in iter))
    if not parts:
        return ""
    elif len(parts) == 1:
        return parts[0]
    elif glue:
        end = parts.pop()
        lead = ", ".join(parts)
        return f"{lead} {glue} {end}"
    else:
        return ", ".join(parts)


def handle_zaken_notification(notification: Notification):
    if notification.kanaal != "zaken":
        raise Exception(
            f"handler expects kanaal 'zaken' but received '{notification.kanaal}'"
        )

    # on the 'zaken' channel the hoofd_object is always the zaak
    case_url = notification.hoofd_object

    # we're only interested in some updates
    resources = ("status", "zaakinformatieobject")
    r = notification.resource  # short alias for logging

    if notification.resource not in resources:
        log_system_action(
            f"ignored {r} notification: resource is not {wrap_join(resources, 'or')} but '{notification.resource}' for case {case_url}",
            log_level=logging.INFO,
        )
        return

    # check if we have users that need to be informed about this case
    roles = fetch_case_roles(case_url)
    if not roles:
        log_system_action(
            f"ignored {r} notification: cannot retrieve rollen for case {case_url}",
            # NOTE this used to be logging.ERROR, but as this is also our first call we get a lot of 403 "Niet geautoriseerd voor zaaktype"
            log_level=logging.INFO,
        )
        return

    inform_users = get_emailable_initiator_users_from_roles(roles)
    if not inform_users:
        log_system_action(
            f"ignored {r} notification: no users with bsn, valid email or with enabled notifications as (mede)initiators in case {case_url}",
            log_level=logging.INFO,
        )
        return

    # check if this case is visible
    case = fetch_case_by_url_no_cache(case_url)
    if not case:
        log_system_action(
            f"ignored {r} notification: cannot retrieve case {case_url}",
            log_level=logging.ERROR,
        )
        return

    case_type = fetch_single_case_type(case.zaaktype)
    if not case_type:
        log_system_action(
            f"ignored {r} notification: cannot retrieve case_type {case.zaaktype} for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    case.zaaktype = case_type

    if not is_zaak_visible(case):
        log_system_action(
            f"ignored {r} notification: case not visible after applying website visibility filter for case {case_url}",
            log_level=logging.INFO,
        )
        return

    if notification.resource == "status":
        _handle_status_notification(notification, case, inform_users)
    elif notification.resource == "zaakinformatieobject":
        _handle_zaakinformatieobject_notification(notification, case, inform_users)
    else:
        raise NotImplementedError("programmer error in earlier resource filter")


def _handle_zaakinformatieobject_notification(
    notification: Notification, case: Zaak, inform_users
):
    oz_config = OpenZaakConfig.get_solo()
    r = notification.resource  # short alias for logging

    """
    {
    "kanaal": "zaken",
    "hoofdObject": "https://test.openzaak.nl/zaken/api/v1/zaken/af715571-a542-4b68-9a46-3821b9589045",
    "resource": "zaakinformatieobject",
    "resourceUrl": "https://test.openzaak.nl/zaken/api/v1/zaakinformatieobjecten/348d0669-0145-48de-859f-29dafa8a885a",
    "actie": "create",
    "aanmaakdatum": "2023-02-06T09:33:17.402799Z",
    "kenmerken": {
        "bronorganisatie": "100000009",
        "zaaktype": "https://test.openzaak.nl/catalogi/api/v1/zaaktypen/2c1feba6-3163-4e15-9afa-fa4f01dcb4f9",
        "vertrouwelijkheidaanduiding": "openbaar"
    }}
    """

    # check if this is a zaakinformatieobject we want to inform on
    ziobj_url = notification.resource_url

    ziobj = fetch_single_case_information_object(ziobj_url)

    if not ziobj:
        log_system_action(
            f"ignored {r} notification: cannot retrieve zaakinformatieobject {ziobj_url} for case {case.url}",
            log_level=logging.ERROR,
        )
        return

    info_object = fetch_single_information_object_url(ziobj.informatieobject)
    if not info_object:
        log_system_action(
            f"ignored {r} notification: cannot retrieve informatieobject {ziobj.informatieobject} for case {case.url}",
            log_level=logging.ERROR,
        )
        return

    ziobj.informatieobject = info_object

    if not is_info_object_visible(info_object, oz_config.document_max_confidentiality):
        log_system_action(
            f"ignored {r} notification: informatieobject not visible after applying website visibility filter for case {case.url}",
            log_level=logging.INFO,
        )
        return

    # NOTE for documents we don't check the statustype.informeren
    ztiotc = get_zaak_type_info_object_type_config(
        case.zaaktype, info_object.informatieobjecttype
    )
    if not ztiotc:
        log_system_action(
            f"ignored {r} notification: cannot retrieve info_type configuration {info_object.informatieobjecttype} and case {case.url}",
            log_level=logging.INFO,
        )
        return
    elif not ztiotc.document_notification_enabled:
        log_system_action(
            f"ignored {r} notification: info_type configuration '{ztiotc.omschrijving}' {info_object.informatieobjecttype} found but 'document_notification_enabled' is False for case {case.url}",
            log_level=logging.INFO,
        )
        return

    # reaching here means we're going to inform users
    log_system_action(
        f"accepted {r} notification: attempt informing users {wrap_join(inform_users)} for case {case.url}",
        log_level=logging.INFO,
    )
    for user in inform_users:
        # TODO run in try/except so it can't bail?
        handle_zaakinformatieobject_update(user, case, ziobj)


def handle_zaakinformatieobject_update(
    user: User, case: Zaak, zaak_info_object: ZaakInformatieObject
):
    # hook into userfeed
    hooks.case_document_added_notification_received(user, case, zaak_info_object)

    note = UserCaseInfoObjectNotification.objects.record_if_unique_notification(
        user,
        case.uuid,
        zaak_info_object.uuid,
    )
    if not note:
        log_system_action(
            f"ignored duplicate zaakinformatieobject notification delivery for user '{user}' zaakinformatieobject {zaak_info_object.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    # let's not spam the users
    period = timedelta(seconds=settings.ZGW_LIMIT_NOTIFICATIONS_FREQUENCY)
    if note.has_received_similar_notes_within(period):
        log_system_action(
            f"blocked over-frequent zaakinformatieobject notification email for user '{user}' zaakinformatieobject {zaak_info_object.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    send_case_update_email(user, case)
    note.mark_sent()

    log_system_action(
        f"send zaakinformatieobject notification email for user '{user}' zaakinformatieobject {zaak_info_object.url} case {case.url}",
        log_level=logging.INFO,
    )


def _handle_status_notification(notification: Notification, case: Zaak, inform_users):
    oz_config = OpenZaakConfig.get_solo()
    r = notification.resource  # short alias for logging

    # check if this is a status we want to inform on
    status_url = notification.resource_url

    status_history = fetch_status_history_no_cache(case.url)
    if not status_history:
        log_system_action(
            f"ignored {r} notification: cannot retrieve status_history for case {case.url}",
            log_level=logging.ERROR,
        )
        return

    if len(status_history) == 1:
        log_system_action(
            f"ignored {r} notification: skip initial status notification for case {case.url}",
            log_level=logging.INFO,
        )
        return

    for s in status_history:
        if s.url == status_url:
            status = s
            break
    else:
        status = fetch_single_status(status_url)

    if not status:
        log_system_action(
            f"ignored {r} notification: cannot retrieve status {status_url} for case {case.url}",
            log_level=logging.ERROR,
        )
        return

    status_type = fetch_single_status_type(status.statustype)
    if not status_type:
        log_system_action(
            f"ignored {r} notification: cannot retrieve status_type {status.statustype} for case {case.url}",
            log_level=logging.ERROR,
        )
        return

    if not oz_config.skip_notification_statustype_informeren:
        if not status_type.informeren:
            log_system_action(
                f"ignored {r} notification: status_type.informeren is false for status {status.url} and case {case.url}",
                log_level=logging.INFO,
            )
            return

    status.statustype = status_type

    # check the ZaakTypeConfig
    ztc = get_zaak_type_config(case.zaaktype)
    if oz_config.skip_notification_statustype_informeren:
        if not ztc:
            log_system_action(
                f"ignored {r} notification: 'skip_notification_statustype_informeren' is True but cannot retrieve case_type configuration '{case.zaaktype.identificatie}' for case {case.url}",
                log_level=logging.INFO,
            )
            return
        elif not ztc.notify_status_changes:
            log_system_action(
                f"ignored {r} notification: case_type configuration '{case.zaaktype.identificatie}' found but 'notify_status_changes' is False for case {case.url}",
                log_level=logging.INFO,
            )
            return

    # check status notification setting on `ZaakTypeStatusTypeConfig`
    resolve_status(case)
    statustype_url = case.status.statustype

    try:
        statustype_config = ZaakTypeStatusTypeConfig.objects.get(
            zaaktype_config=ztc, statustype_url=statustype_url
        )
    except ZaakTypeStatusTypeConfig.DoesNotExist:
        pass
    else:
        if not statustype_config.notify_status_change:
            log_system_action(
                f"ignored {r} notification: 'notify_status_change' is False for the status "
                f"type configuration of the status of this case ({case.url})",
                log_level=logging.INFO,
            )
            return

    # reaching here means we're going to inform users
    log_system_action(
        f"accepted {r} notification: attempt informing users {wrap_join(inform_users)} for case {case.url}",
        log_level=logging.INFO,
    )
    for user in inform_users:
        handle_status_update(user, case, status)


def handle_status_update(user: User, case: Zaak, status: Status):
    # hook into userfeed
    hooks.case_status_notification_received(user, case, status)

    # email notification
    note = UserCaseStatusNotification.objects.record_if_unique_notification(
        user,
        case.uuid,
        status.uuid,
    )
    if not note:
        log_system_action(
            f"ignored duplicate status notification delivery for user '{user}' status {status.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    # let's not spam the users
    period = timedelta(seconds=settings.ZGW_LIMIT_NOTIFICATIONS_FREQUENCY)
    if note.has_received_similar_notes_within(period):
        log_system_action(
            f"blocked over-frequent status notification email for user '{user}' status {status.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    send_case_update_email(user, case)
    note.mark_sent()

    log_system_action(
        f"send status notification email for user '{user}' status {status.url} case {case.url}",
        log_level=logging.INFO,
    )


def send_case_update_email(user: User, case: Zaak):
    """
    send the actual mail
    """
    case_detail_url = build_absolute_url(
        reverse("cases:case_detail", kwargs={"object_id": str(case.uuid)})
    )

    template = find_template("case_notification")
    context = {
        "identification": case.identification,
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


def get_nnp_initiator_nnp_id_from_roles(roles: List[Rol]) -> List[str]:
    """
    iterate over Rollen and for all non-natural-person initiators return their nnpId
    """
    ret = set()

    for role in roles:
        if role.omschrijving_generiek not in (
            RolOmschrijving.initiator,
            RolOmschrijving.medeinitiator,
        ):
            continue
        if role.betrokkene_type != RolTypes.niet_natuurlijk_persoon:
            continue
        if not role.betrokkene_identificatie:
            continue
        nnp_id = role.betrokkene_identificatie.get("inn_nnp_id")
        if not nnp_id:
            continue
        ret.add(nnp_id)

    return list(ret)


def get_emailable_initiator_users_from_roles(roles: List[Rol]) -> List[User]:
    """
    iterate over Rollen and return User objects for all natural-person initiators we can notify
    """
    users = []

    bsn_list = get_np_initiator_bsns_from_roles(roles)
    if bsn_list:
        users += list(
            User.objects.filter(
                bsn__in=bsn_list, is_active=True, cases_notifications=True
            ).having_usable_email()
        )

    nnp_id_list = get_nnp_initiator_nnp_id_from_roles(roles)
    if nnp_id_list:
        config = OpenZaakConfig.get_solo()
        if config.fetch_eherkenning_zaken_with_rsin:
            id_filter = {"rsin__in": nnp_id_list}
        else:
            id_filter = {"kvk__in": nnp_id_list}
        users += list(
            User.objects.filter(
                is_active=True, cases_notifications=True, **id_filter
            ).having_usable_email()
        )

    return users
