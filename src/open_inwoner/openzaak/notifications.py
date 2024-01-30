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
    ZaakType,
)
from open_inwoner.openzaak.cases import resolve_status
from open_inwoner.openzaak.clients import CatalogiClient, ZakenClient, build_client
from open_inwoner.openzaak.documents import fetch_single_information_object_url
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    UserCaseInfoObjectNotification,
    UserCaseStatusNotification,
    ZaakTypeConfig,
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

    client = build_client("zaak")
    if not client:
        log_system_action(
            f"ignored {r} notification: cannot build Zaken API client for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    if notification.resource not in resources:
        log_system_action(
            f"ignored {r} notification: resource is not {wrap_join(resources, 'or')} but '{notification.resource}' for case {case_url}",
            log_level=logging.INFO,
        )
        return

    # check if we have users that need to be informed about this case
    roles = client.fetch_case_roles(case_url)
    if not roles:
        log_system_action(
            f"ignored {r} notification: cannot retrieve rollen for case {case_url}",
            # NOTE this used to be logging.ERROR, but as this is also our first call we get a lot of 403 "Niet geautoriseerd voor zaaktype"
            log_level=logging.INFO,
        )
        return

    inform_users = get_initiator_users_from_roles(roles)
    if not inform_users:
        log_system_action(
            f"ignored {r} notification: no users with bsn/nnp_id as (mede)initiators in case {case_url}",
            log_level=logging.INFO,
        )
        return

    # check if this case is visible
    case = client.fetch_case_by_url_no_cache(case_url)
    if not case:
        log_system_action(
            f"ignored {r} notification: cannot retrieve case {case_url}",
            log_level=logging.ERROR,
        )
        return

    case_type = None
    if catalogi_client := build_client("catalogi"):
        case_type = catalogi_client.fetch_single_case_type(case.zaaktype)

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
        handle_status_notification(notification, case, inform_users)
    elif notification.resource == "zaakinformatieobject":
        _handle_zaakinformatieobject_notification(notification, case, inform_users)
    else:
        raise NotImplementedError("programmer error in earlier resource filter")


def _handle_zaakinformatieobject_notification(
    notification: Notification, case: Zaak, inform_users
):
    oz_config = OpenZaakConfig.get_solo()
    r = notification.resource  # short alias for logging

    client = build_client("zaak")
    if not client:
        log_system_action(
            f"ignored {r} notification: cannot build Zaken API client for case {case.url}",
            log_level=logging.ERROR,
        )
        return

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

    ziobj = client.fetch_single_case_information_object(ziobj_url)

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

    if not user.cases_notifications or not user.get_contact_email():
        log_system_action(
            f"ignored user-disabled notification delivery for user '{user}' zaakinformatieobject {zaak_info_object.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

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

    send_case_update_email(user, case, "case_document_notification")
    note.mark_sent()

    log_system_action(
        f"send zaakinformatieobject notification email for user '{user}' zaakinformatieobject {zaak_info_object.url} case {case.url}",
        log_level=logging.INFO,
    )


#
# Helper functions for handling status update notifications
#
def check_status_history(
    notification: Notification, case: Zaak, client: ZakenClient
) -> List[Status] | None:
    """
    Check if more than one status exists for `case` (else notifications are skipped)
    """
    resource = notification.resource
    status_history = client.fetch_status_history_no_cache(case.url)

    if not status_history:
        log_system_action(
            f"ignored {resource} notification: cannot retrieve status_history for case {case.url}",
            log_level=logging.ERROR,
        )
        return None

    if len(status_history) == 1:
        log_system_action(
            f"ignored {resource} notification: skip initial status notification for case {case.url}",
            log_level=logging.INFO,
        )
        return None

    return status_history


def check_status(
    notification: Notification,
    case: Zaak,
    status_history: List[Status],
    client: ZakenClient,
) -> Status | None:
    """
    Check if this is a status we want to inform on
    """
    resource = notification.resource
    status_url = notification.resource_url

    for s in status_history:
        if s.url == status_url:
            status = s
            break
    else:
        # TODO currently not covered in tests?
        if client:
            status = client.fetch_single_status(status_url)

    if not status:
        log_system_action(
            f"ignored {resource} notification: cannot retrieve status {status_url} for case {case.url}",
            log_level=logging.ERROR,
        )
        return None

    return status


def check_status_type(
    notification: Notification,
    case: Zaak,
    status: Status,
    oz_config: OpenZaakConfig,
    catalogi_client: CatalogiClient,
) -> ZaakType | None:
    """
    Check if a status_type exists for `status` and if notifications are enabled
    """
    status_type = catalogi_client.fetch_single_status_type(status.statustype)
    resource = notification.resource

    if not status_type:
        log_system_action(
            f"ignored {resource} notification: cannot retrieve status_type "
            f"{status.statustype} for case {case.url}",
            log_level=logging.ERROR,
        )
        return None

    if (
        not oz_config.skip_notification_statustype_informeren
        and not status_type.informeren
    ):
        log_system_action(
            f"ignored {resource} notification: status_type.informeren is false for "
            f"status {status.url} and case {case.url}",
            log_level=logging.INFO,
        )
        return None

    return status_type


def check_zaaktype_config(
    notification: Notification,
    case: Zaak,
    oz_config: OpenZaakConfig,
) -> ZaakTypeConfig | None:
    """
    Check if zaaktype_config exists and notifications are enabled
    """
    resource = notification.resource
    ztc = get_zaak_type_config(case.zaaktype)

    if oz_config.skip_notification_statustype_informeren:
        if not ztc:
            log_system_action(
                f"ignored {resource} notification: 'skip_notification_statustype_informeren' "
                f"is True but cannot retrieve case_type configuration '{case.zaaktype.identificatie}' "
                f"for case {case.url}",
                log_level=logging.INFO,
            )
            return None
        elif not ztc.notify_status_changes:
            log_system_action(
                f"ignored {resource} notification: case_type configuration "
                f"'{case.zaaktype.identificatie}' found but 'notify_status_changes' is False "
                f"for case {case.url}",
                log_level=logging.INFO,
            )
            return None

    return ztc


def check_statustype_config(
    notification: Notification,
    case: Zaak,
    ztc: ZaakTypeConfig,
) -> ZaakTypeStatusTypeConfig | None:
    """
    Check if statustype_config exists and notifications are enabled
    """
    resource = notification.resource
    statustype_url = case.status.statustype

    try:
        statustype_config = ZaakTypeStatusTypeConfig.objects.get(
            zaaktype_config=ztc, statustype_url=statustype_url
        )
    except ZaakTypeStatusTypeConfig.DoesNotExist:
        log_system_action(
            "ignored {resource} notification: ZaakTypeStatusTypeConfig could not be found for statustype {url}",
            resource=resource,
            url=statustype_url,
            log_level=logging.INFO,
        )
        return None

    if not statustype_config.notify_status_change:
        log_system_action(
            f"ignored {resource} notification: 'notify_status_change' is False for "
            f"the status type configuration of the status of this case ({case.url})",
            log_level=logging.INFO,
        )
        return None

    return statustype_config


def check_user_status_notitifactions(
    user: User,
    case: Zaak,
    status: Status,
    status_type_config: ZaakTypeStatusTypeConfig,
) -> bool:
    """
    Check if user has an email and status notifications are enabled

    The user cannot opt out of action-required-notifications
    """
    if status_type_config.action_required:
        return True

    if not user.cases_notifications or not user.get_contact_email():
        log_system_action(
            f"ignored user-disabled notification delivery for user '{user}' status "
            f"{status.url} case {case.url}",
            log_level=logging.INFO,
        )
        return False

    return True


def handle_status_notification(
    notification: Notification,
    case: Zaak,
    inform_users: list[User],
):
    """
    Check status notification settings of user and case-related objects/configs
    """
    oz_config = OpenZaakConfig.get_solo()

    catalogi_client = build_client("catalogi")
    if not catalogi_client:
        log_system_action(
            f"ignored {notification.resource} notification for {case.url}: cannot create Catalogi API client",
            log_level=logging.ERROR,
        )
        return None

    zaken_client = build_client("zaak")
    if not zaken_client:
        log_system_action(
            f"ignored {notification.resource} notification for {case.url}: cannot create Zaken API client",
            log_level=logging.ERROR,
        )
        return

    if not (status_history := check_status_history(notification, case, zaken_client)):
        return

    if not (status := check_status(notification, case, status_history, zaken_client)):
        return

    if not (
        status_type := check_status_type(
            notification, case, status, oz_config, catalogi_client
        )
    ):
        return

    if not (ztc := check_zaaktype_config(notification, case, oz_config)):
        return

    resolve_status(case, client=zaken_client)
    if not (status_type_config := check_statustype_config(notification, case, ztc)):
        return

    status.statustype = status_type

    for user in inform_users:
        if not check_user_status_notitifactions(user, case, status, status_type_config):
            return

        # all checks have passed
        log_system_action(
            f"accepted {notification.resource} notification: attempt informing users "
            f"{wrap_join(inform_users)} for case {case.url}",
            log_level=logging.INFO,
        )
        handle_status_update(user, case, status, status_type_config)


def handle_status_update(
    user: User,
    case: Zaak,
    status: Status,
    status_type_config: ZaakTypeStatusTypeConfig,
):
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
            f"ignored duplicate status notification delivery for user '{user}' status "
            f"{status.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    # let's not spam the users
    period = timedelta(seconds=settings.ZGW_LIMIT_NOTIFICATIONS_FREQUENCY)
    if note.has_received_similar_notes_within(period):
        log_system_action(
            f"blocked over-frequent status notification email for user '{user}' status "
            f"{status.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    # choose template
    if status_type_config.action_required:
        template_name = "case_status_notification_action_required"
    else:
        template_name = "case_status_notification"

    send_case_update_email(user, case, template_name)
    note.mark_sent()

    log_system_action(
        f"send status notification email for user '{user}' status {status.url} case {case.url}",
        log_level=logging.INFO,
    )


def send_case_update_email(
    user: User, case: Zaak, template_name: str, extra_context: dict = None
):
    """
    send the actual mail
    """
    case_detail_url = build_absolute_url(
        reverse("cases:case_detail", kwargs={"object_id": str(case.uuid)})
    )

    template = find_template(template_name)
    context = {
        "identification": case.identification,
        "type_description": case.zaaktype.omschrijving,
        "start_date": case.startdatum,
        "end_date": case.einddatum_gepland,
        "case_link": case_detail_url,
    }
    if extra_context:
        context.update(extra_context)
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


def get_initiator_users_from_roles(roles: List[Rol]) -> List[User]:
    """
    iterate over Rollen and return User objects for initiators
    """
    users = []

    bsn_list = get_np_initiator_bsns_from_roles(roles)
    if bsn_list:
        users += list(User.objects.filter(bsn__in=bsn_list, is_active=True))

    nnp_id_list = get_nnp_initiator_nnp_id_from_roles(roles)
    if nnp_id_list:
        config = OpenZaakConfig.get_solo()
        if config.fetch_eherkenning_zaken_with_rsin:
            id_filter = {"rsin__in": nnp_id_list}
        else:
            id_filter = {"kvk__in": nnp_id_list}
        users += list(User.objects.filter(is_active=True, **id_filter))

    return users
