import logging
from datetime import date, timedelta

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _

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
from open_inwoner.openzaak.clients import (
    CatalogiClient,
    ZakenClient,
    build_catalogi_client,
    build_zaken_client,
)
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

from .models import ZaakTypeStatusTypeConfig, ZGWApiGroupConfig

logger = logging.getLogger(__name__)


# TODO: check siteconfig for notification enabled
def handle_zaken_notification(notification: Notification):
    """
    Perform basic checks, then dispatch to
        - `handle_status_notification` or
        - `handle_zaakinformatieobject_notification`
    """
    if notification.kanaal != "zaken":
        raise Exception(
            f"handler expects kanaal 'zaken' but received '{notification.kanaal}'"
        )

    # on the 'zaken' channel the hoofd_object is always the zaak
    case_url = notification.hoofd_object

    # we're only interested in some updates
    resources = ("status", "zaakinformatieobject")
    r = notification.resource  # short alias for logging

    client = build_zaken_client()
    if not client:
        log_system_action(
            f"ignored {r} notification: cannot build Zaken API client for case {case_url}",
            log_level=logging.ERROR,
        )
        return

    if notification.resource not in resources:
        log_system_action(
            f"ignored {r} notification: resource is not "
            f"{_wrap_join(resources, 'or')} but '{notification.resource}' for case {case_url}",
            log_level=logging.INFO,
        )
        return

    # check if we have users that need to be informed about this case
    roles = client.fetch_case_roles(case_url)
    if not roles:
        log_system_action(
            f"ignored {r} notification: cannot retrieve rollen for case {case_url}",
            # NOTE this used to be logging.ERROR, but as this is also our first call
            # we get a lot of 403 "Niet geautoriseerd voor zaaktype"
            log_level=logging.INFO,
        )
        return

    inform_users = _get_initiator_users_from_roles(roles)
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
    if catalogi_client := build_catalogi_client():
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
            f"ignored {r} notification: case not visible after applying website "
            f"visibility filter for case {case_url}",
            log_level=logging.INFO,
        )
        return

    if notification.resource == "status":
        _handle_status_notification(notification, case, inform_users)
    elif notification.resource == "zaakinformatieobject":
        _handle_zaakinformatieobject_notification(notification, case, inform_users)
    else:
        raise NotImplementedError("programmer error in earlier resource filter")


def send_case_update_email(
    user: User,
    case: Zaak,
    template_name: str,
    status: Status | None = None,
    extra_context: dict = None,
):
    group = ZGWApiGroupConfig.objects.resolve_group_from_hints(url=case.url)

    """
    send the actual mail
    """
    case_detail_url = build_absolute_url(
        reverse(
            "cases:case_detail",
            kwargs={"object_id": str(case.uuid), "api_group_id": group.id},
        )
    )

    config = OpenZaakConfig.get_solo()

    template = find_template(template_name)
    context = {
        "identification": case.identification,
        "type_description": case.zaaktype.omschrijving,
        "start_date": case.startdatum,
        "end_date": date.today() + timedelta(days=config.action_required_deadline_days),
        "case_link": case_detail_url,
    }
    if status:
        status_type = status.statustype
        context["status_description"] = (
            status_type.statustekst
            or status_type.omschrijving
            or _("No data available")
        )
    if extra_context:
        context.update(extra_context)
    template.send_email([user.email], context)


def _wrap_join(iter, glue="") -> str:
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


#
# Helper functions for ZaakInformatieObject notifications
#
def _handle_zaakinformatieobject_notification(
    notification: Notification, case: Zaak, inform_users
):
    oz_config = OpenZaakConfig.get_solo()
    r = notification.resource  # short alias for logging

    client = build_zaken_client()
    if not client:
        log_system_action(
            f"ignored {r} notification: cannot build Zaken API client for case {case.url}",
            log_level=logging.ERROR,
        )
        return

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
            f"ignored {r} notification: cannot retrieve informatieobject "
            f"{ziobj.informatieobject} for case {case.url}",
            log_level=logging.ERROR,
        )
        return

    ziobj.informatieobject = info_object

    if not is_info_object_visible(info_object, oz_config.document_max_confidentiality):
        log_system_action(
            f"ignored {r} notification: informatieobject not visible after "
            f"applying website visibility filter for case {case.url}",
            log_level=logging.INFO,
        )
        return

    # NOTE for documents we don't check the statustype.informeren
    ztiotc = get_zaak_type_info_object_type_config(
        case.zaaktype, info_object.informatieobjecttype
    )
    if not ztiotc:
        log_system_action(
            f"ignored {r} notification: cannot retrieve info_type "
            f"configuration {info_object.informatieobjecttype} and case {case.url}",
            log_level=logging.INFO,
        )
        return
    elif not ztiotc.document_notification_enabled:
        log_system_action(
            f"ignored {r} notification: info_type configuration "
            f"'{ztiotc.omschrijving}' {info_object.informatieobjecttype} "
            f"found but 'document_notification_enabled' is False for case {case.url}",
            log_level=logging.INFO,
        )
        return

    # reaching here means we're going to inform users
    log_system_action(
        f"accepted {r} notification: attempt informing users {_wrap_join(inform_users)} for case {case.url}",
        log_level=logging.INFO,
    )
    for user in inform_users:
        _handle_zaakinformatieobject_update(user, case, ziobj)


def _handle_zaakinformatieobject_update(
    user: User, case: Zaak, zaak_info_object: ZaakInformatieObject
):
    template_name = "case_document_notification"

    # hook into userfeed
    hooks.case_document_added_notification_received(user, case, zaak_info_object)

    if not user.cases_notifications or not user.get_contact_email():
        log_system_action(
            f"ignored user-disabled notification delivery for user "
            f"'{user}' zaakinformatieobject {zaak_info_object.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    note = UserCaseInfoObjectNotification.objects.record_if_unique_notification(
        user,
        case.uuid,
        zaak_info_object.uuid,
        template_name,
    )
    if not note:
        log_system_action(
            f"ignored duplicate zaakinformatieobject notification delivery "
            f"for user '{user}' zaakinformatieobject {zaak_info_object.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    # let's not spam the users
    period = timedelta(seconds=settings.ZGW_LIMIT_NOTIFICATIONS_FREQUENCY)
    if note.has_received_similar_notes_within(period, template_name):
        log_system_action(
            f"blocked over-frequent zaakinformatieobject notification email "
            f"for user '{user}' zaakinformatieobject {zaak_info_object.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    send_case_update_email(user, case, template_name)
    note.mark_sent()

    log_system_action(
        f"send zaakinformatieobject notification email for user '{user}' "
        f"zaakinformatieobject {zaak_info_object.url} case {case.url}",
        log_level=logging.INFO,
    )


#
# Helper functions for status update notifications
#
def _check_status_history(
    notification: Notification, case: Zaak, client: ZakenClient
) -> list[Status] | None:
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


def _check_status(
    notification: Notification,
    case: Zaak,
    status_history: list[Status],
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


def _check_status_type(
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


def _check_zaaktype_config(
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


def _check_statustype_config(
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


def _check_user_status_notitifactions(
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


def _handle_status_notification(
    notification: Notification,
    case: Zaak,
    inform_users: list[User],
):
    """
    Check status notification settings of user and case-related objects/configs
    """
    oz_config = OpenZaakConfig.get_solo()

    catalogi_client = build_catalogi_client()
    if not catalogi_client:
        log_system_action(
            f"ignored {notification.resource} notification for {case.url}: cannot create Catalogi API client",
            log_level=logging.ERROR,
        )
        return None

    zaken_client = build_zaken_client()
    if not zaken_client:
        log_system_action(
            f"ignored {notification.resource} notification for {case.url}: cannot create Zaken API client",
            log_level=logging.ERROR,
        )
        return

    if not (status_history := _check_status_history(notification, case, zaken_client)):
        return

    if not (status := _check_status(notification, case, status_history, zaken_client)):
        return

    if not (
        status_type := _check_status_type(
            notification, case, status, oz_config, catalogi_client
        )
    ):
        return

    if not (ztc := _check_zaaktype_config(notification, case, oz_config)):
        return

    resolve_status(case, client=zaken_client)
    if not (status_type_config := _check_statustype_config(notification, case, ztc)):
        return

    status.statustype = status_type

    for user in inform_users:
        if not _check_user_status_notitifactions(
            user, case, status, status_type_config
        ):
            return

        # all checks have passed
        log_system_action(
            f"accepted {notification.resource} notification: attempt informing users "
            f"{_wrap_join(inform_users)} for case {case.url}",
            log_level=logging.INFO,
        )
        # TODO: replace with notify_about_status_update(...args, method: Callable)
        _handle_status_update(user, case, status, status_type_config)


def _handle_status_update(
    user: User,
    case: Zaak,
    status: Status,
    status_type_config: ZaakTypeStatusTypeConfig,
):
    # choose template
    if status_type_config.action_required:
        template_name = "case_status_notification_action_required"
    else:
        template_name = "case_status_notification"

    # hook into userfeed
    hooks.case_status_notification_received(user, case, status)

    # email notification
    note = UserCaseStatusNotification.objects.record_if_unique_notification(
        user,
        case.uuid,
        status.uuid,
        template_name,
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
    if note.has_received_similar_notes_within(period, template_name):
        log_system_action(
            f"blocked over-frequent status notification email for user '{user}' status "
            f"{status.url} case {case.url}",
            log_level=logging.INFO,
        )
        return

    send_case_update_email(user, case, template_name, status=status)
    note.mark_sent()

    log_system_action(
        f"send status notification email for user '{user}' status {status.url} case {case.url}",
        log_level=logging.INFO,
    )


# - - - - -


def _get_np_initiator_bsns_from_roles(roles: list[Rol]) -> list[str]:
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


def _get_nnp_initiator_nnp_id_from_roles(roles: list[Rol]) -> list[str]:
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


def _get_initiator_users_from_roles(roles: list[Rol]) -> list[User]:
    """
    iterate over Rollen and return User objects for initiators
    """
    users = []

    bsn_list = _get_np_initiator_bsns_from_roles(roles)
    if bsn_list:
        users += list(User.objects.filter(bsn__in=bsn_list, is_active=True))

    nnp_id_list = _get_nnp_initiator_nnp_id_from_roles(roles)
    if nnp_id_list:
        config = OpenZaakConfig.get_solo()
        if config.fetch_eherkenning_zaken_with_rsin:
            id_filter = {"rsin__in": nnp_id_list}
        else:
            id_filter = {"kvk__in": nnp_id_list}
        users += list(User.objects.filter(is_active=True, **id_filter))

    return users
