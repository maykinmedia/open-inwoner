import logging  # noqa: TID251 - only used for log levels
from datetime import date, timedelta

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _

import structlog
from mail_editor.helpers import find_template
from requests import RequestException
from zgw_consumers.api_models.constants import RolOmschrijving, RolTypes

from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import (
    Notification,
    Rol,
    Status,
    StatusType,
    Zaak,
    ZaakInformatieObject,
)
from open_inwoner.openzaak.exceptions import ZgwAPIError
from open_inwoner.openzaak.mixins import WebhookLogMixin
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    UserCaseInfoObjectNotification,
    UserCaseStatusNotification,
    ZaakTypeConfig,
    ZaakTypeStatusTypeConfig,
    ZGWApiGroupConfig,
)
from open_inwoner.openzaak.services import ZGWService
from open_inwoner.openzaak.utils import (
    get_zaak_type_config,
    get_zaak_type_info_object_type_config,
    is_info_object_visible,
)
from open_inwoner.userfeed import hooks
from open_inwoner.utils.logentry import system_action as log_system_action
from open_inwoner.utils.url import build_absolute_url

logger = structlog.stdlib.get_logger(__name__)

# Create a helper instance for logging
_log_helper = WebhookLogMixin()


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
    zaak_url = notification.hoofd_object

    # we're only interested in some updates
    resources = ("status", "zaakinformatieobject")
    r = notification.resource  # short alias for logging

    if notification.resource not in resources:
        log_system_action(
            f"ignored {r} notification: resource is not "
            f"{_wrap_join(resources, 'or')} but '{notification.resource}' for zaak {zaak_url}",
            log_level=logging.INFO,
        )
        return

    try:
        api_group = ZGWApiGroupConfig.objects.resolve_group_from_hints(url=zaak_url)
    except ZGWApiGroupConfig.DoesNotExist:
        logger.error("No API group defined for zaak", zaak_url=zaak_url)
        return

    service = ZGWService(use_cache=False)

    # check if we have users that need to be informed about this case
    try:
        roles = service.fetch_zaak_roles(zaak_url, api_group)
    except (ZgwAPIError, RequestException):
        log_system_action(
            f"ignored {r} notification: cannot retrieve rollen for zaak {zaak_url}",
            # NOTE this used to be logging.ERROR, but as this is also our first call
            # we get a lot of 403 "Niet geautoriseerd voor zaaktype"
            log_level=logging.INFO,
        )
        return

    config = OpenZaakConfig.get_solo()
    inform_users = _get_initiator_users_from_roles(
        roles,
        api_group=api_group,
        limit_access_to_role=config.limit_user_visible_cases_to_role,
    )
    if not inform_users:
        log_system_action(
            f"ignored {r} notification: no users with bsn/nnp_id as (mede)initiators in zaak {zaak_url}",
            log_level=logging.INFO,
        )
        return

    # check if this case is visible
    try:
        zaak = service.fetch_zaak_by_url(zaak_url, api_group)
    except (ZgwAPIError, RequestException):
        log_system_action(
            f"ignored {r} notification: cannot retrieve zaak {zaak_url}",
            log_level=logging.ERROR,
        )
        return

    zaaktype_url = zaak.zaaktype  # URL string before resolution
    try:
        zaaktype = service.fetch_zaaktype_by_url(zaaktype_url, api_group)
    except (ZgwAPIError, RequestException):
        log_system_action(
            f"ignored {r} notification: cannot retrieve zaaktype {zaaktype_url}",
            log_level=logging.ERROR,
        )
        return
    zaak.zaaktype = zaaktype

    if not service._is_zaak_visible(zaak)[0]:
        log_system_action(
            f"ignored {r} notification: zaak not visible after applying website "
            f"visibility filter for zaak {zaak_url}",
            log_level=logging.INFO,
        )
        return

    if notification.resource == "status":
        _handle_status_notification(
            notification, zaak, inform_users, api_group, service
        )
    elif notification.resource == "zaakinformatieobject":
        _handle_zaakinformatieobject_notification(
            notification, zaak, inform_users, api_group
        )
    else:
        raise NotImplementedError("programmer error in earlier resource filter")


def send_case_update_email(
    user: User,
    zaak: Zaak,
    template_name: str,
    api_group: ZGWApiGroupConfig,
    status: Status | None = None,
    extra_context: dict = None,
):
    """
    send the actual mail
    """
    case_detail_url = build_absolute_url(
        reverse(
            "cases:case_detail",
            kwargs={"object_id": str(zaak.uuid), "api_group_id": api_group.id},
        )
    )

    config = OpenZaakConfig.get_solo()

    template = find_template(template_name)
    context = {
        "identification": zaak.identification,
        "case_description": zaak.omschrijving,
        "type_description": zaak.zaaktype.omschrijving,
        "start_date": zaak.startdatum,
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
    notification: Notification,
    zaak: Zaak,
    inform_users: list[User],
    api_group: ZGWApiGroupConfig,
):
    oz_config = api_group.open_zaak_config
    r = notification.resource  # short alias for logging

    # check if this is a zaakinformatieobject we want to inform on
    ziobj_url = notification.resource_url
    service = ZGWService(use_cache=False)

    try:
        ziobj = service.fetch_single_zaak_information_object(ziobj_url, api_group)
    except (ZgwAPIError, RequestException):
        log_system_action(
            f"ignored {r} notification: cannot retrieve zaakinformatieobject "
            f"{ziobj_url} for zaak {zaak.url}",
            log_level=logging.ERROR,
        )
        return

    try:
        info_object = service.fetch_information_object_by_url(
            ziobj.informatieobject, api_group
        )
    except ZgwAPIError:
        log_system_action(
            f"ignored {r} notification: cannot retrieve informatieobject "
            f"{ziobj.informatieobject} for zaak {zaak.url}",
            log_level=logging.ERROR,
        )
        return

    ziobj.informatieobject = info_object

    if not is_info_object_visible(info_object, oz_config.document_max_confidentiality):
        log_system_action(
            f"ignored {r} notification: informatieobject not visible after "
            f"applying website visibility filter for zaak {zaak.url}",
            log_level=logging.INFO,
        )
        return

    # NOTE for documents we don't check the statustype.informeren
    ztiotc = get_zaak_type_info_object_type_config(
        zaak.zaaktype, info_object.informatieobjecttype
    )
    if not ztiotc:
        log_system_action(
            f"ignored {r} notification: cannot retrieve info_type "
            f"configuration {info_object.informatieobjecttype} and zaak {zaak.url}",
            log_level=logging.INFO,
        )
        return
    elif not ztiotc.document_notification_enabled:
        log_system_action(
            f"ignored {r} notification: info_type configuration "
            f"'{ztiotc.omschrijving}' {info_object.informatieobjecttype} "
            f"found but 'document_notification_enabled' is False for zaak {zaak.url}",
            log_level=logging.INFO,
        )
        return

    # reaching here means we're going to inform users
    _log_helper.log_notification_accepted(notification, inform_users, zaak.url)
    for user in inform_users:
        _handle_zaakinformatieobject_update(notification, user, zaak, ziobj, api_group)


def _handle_zaakinformatieobject_update(
    notification: Notification,
    user: User,
    zaak: Zaak,
    zaak_info_object: ZaakInformatieObject,
    api_group: ZGWApiGroupConfig,
):
    template_name = "case_document_notification"

    # hook into userfeed
    hooks.case_document_added_notification_received(user, zaak, zaak_info_object)

    if not user.cases_notifications or not user.get_contact_email():
        _log_helper.log_notification_email_blocked_by_user(
            notification, user, zaak_info_object.url, zaak.url
        )
        return

    note = UserCaseInfoObjectNotification.objects.record_if_unique_notification(
        user,
        zaak.uuid,
        zaak_info_object.uuid,
        template_name,
    )
    if not note:
        _log_helper.log_notification_email_duplicate(
            notification, user, zaak_info_object.url, zaak.url
        )
        return

    # let's not spam the users
    period = timedelta(seconds=settings.ZGW_LIMIT_NOTIFICATIONS_FREQUENCY)
    if note.has_received_similar_notes_within(period, template_name):
        _log_helper.log_notification_email_rate_limited(
            notification, user, zaak_info_object.url, zaak.url
        )
        return

    send_case_update_email(user, zaak, template_name, api_group=api_group)
    note.mark_sent()

    _log_helper.log_notification_email_sent(
        notification, user, zaak_info_object.url, zaak.url
    )


#
# Helper functions for status update notifications
#
def _check_status_history(
    notification: Notification,
    zaak: Zaak,
    service: ZGWService,
    api_group: ZGWApiGroupConfig,
) -> list[Status] | None:
    """
    Check if more than one status exists for `zaak` (else notifications are skipped)
    """
    resource = notification.resource
    try:
        status_history = service.fetch_status_history(zaak.url, api_group)
    except (ZgwAPIError, RequestException):
        log_system_action(
            f"ignored {resource} notification: cannot retrieve status_history for zaak {zaak.url}",
            log_level=logging.ERROR,
        )
        return None

    if not status_history:
        log_system_action(
            f"ignored {resource} notification: cannot retrieve status_history for zaak {zaak.url}",
            log_level=logging.ERROR,
        )
        return None

    if len(status_history) == 1:
        log_system_action(
            f"ignored {resource} notification: skip initial status notification for zaak {zaak.url}",
            log_level=logging.INFO,
        )
        return None

    return status_history


def _check_status(
    notification: Notification,
    zaak: Zaak,
    status_history: list[Status],
    service: ZGWService,
    api_group: ZGWApiGroupConfig,
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
        status = service.fetch_single_status(status_url, api_group)

    if not status:
        log_system_action(
            f"ignored {resource} notification: cannot retrieve status {status_url} for zaak {zaak.url}",
            log_level=logging.ERROR,
        )
        return None

    return status


def _check_status_type(
    notification: Notification,
    zaak: Zaak,
    status: Status,
    oz_config: OpenZaakConfig,
    service: ZGWService,
    api_group: ZGWApiGroupConfig,
) -> StatusType | None:
    """
    Check if a status_type exists for `status` and if notifications are enabled
    """
    resource = notification.resource

    try:
        status_type = service.fetch_single_status_type(status.statustype, api_group)
    except (ZgwAPIError, RequestException):
        log_system_action(
            f"ignored {resource} notification: cannot retrieve status_type "
            f"{status.statustype} for zaak {zaak.url}",
            log_level=logging.ERROR,
        )
        return None

    if (
        not oz_config.skip_notification_statustype_informeren
        and not status_type.informeren
    ):
        log_system_action(
            f"ignored {resource} notification: status_type.informeren is false for "
            f"status {status.url} and zaak {zaak.url}",
            log_level=logging.INFO,
        )
        return None

    return status_type


def _check_zaaktype_config(
    notification: Notification,
    zaak: Zaak,
    oz_config: OpenZaakConfig,
) -> ZaakTypeConfig | None:
    """
    Check if zaaktype_config exists and notifications are enabled
    """
    resource = notification.resource
    ztc = get_zaak_type_config(zaak.zaaktype)

    if oz_config.skip_notification_statustype_informeren:
        if not ztc:
            log_system_action(
                f"ignored {resource} notification: 'skip_notification_statustype_informeren' "
                f"is True but cannot retrieve zaaktype configuration '{zaak.zaaktype.identificatie}' "
                f"for zaak {zaak.url}",
                log_level=logging.INFO,
            )
            return None
        elif not ztc.notify_status_changes:
            log_system_action(
                f"ignored {resource} notification: zaaktype configuration "
                f"'{zaak.zaaktype.identificatie}' found but 'notify_status_changes' is False "
                f"for zaak {zaak.url}",
                log_level=logging.INFO,
            )
            return None

    return ztc


def _check_statustype_config(
    notification: Notification,
    zaak: Zaak,
    ztc: ZaakTypeConfig,
) -> ZaakTypeStatusTypeConfig | None:
    """
    Check if statustype_config exists and notifications are enabled
    """
    resource = notification.resource
    statustype_url = zaak.status.statustype

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
            f"the status type configuration of the status of this zaak ({zaak.url})",
            log_level=logging.INFO,
        )
        return None

    return statustype_config


def _check_user_status_notitifactions(
    notification: Notification,
    user: User,
    zaak: Zaak,
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
        _log_helper.log_notification_email_blocked_by_user(
            notification, user, status.url, zaak.url
        )
        return False

    return True


def _handle_status_notification(
    notification: Notification,
    zaak: Zaak,
    inform_users: list[User],
    api_group: ZGWApiGroupConfig,
    service: ZGWService,
):
    """
    Check status notification settings of user and case-related objects/configs
    """
    oz_config = api_group.open_zaak_config

    if not (
        status_history := _check_status_history(notification, zaak, service, api_group)
    ):
        return

    if not (
        status := _check_status(notification, zaak, status_history, service, api_group)
    ):
        return

    if not (
        status_type := _check_status_type(
            notification, zaak, status, oz_config, service, api_group
        )
    ):
        return

    if not (ztc := _check_zaaktype_config(notification, zaak, oz_config)):
        return

    status = service.fetch_single_status(zaak.status, api_group)
    if not status:
        # TODO: check if should we return or continue if the case has no status
        logger.error("Unable to fetch status", status_url=zaak.status)
        return

    zaak.status = status
    if not (status_type_config := _check_statustype_config(notification, zaak, ztc)):
        return

    status.statustype = status_type

    for user in inform_users:
        if not _check_user_status_notitifactions(
            notification, user, zaak, status, status_type_config
        ):
            return

        # all checks have passed
        _log_helper.log_notification_accepted(notification, inform_users, zaak.url)
        # TODO: replace with notify_about_status_update(...args, method: Callable)
        _handle_status_update(
            notification, user, zaak, status, status_type_config, api_group
        )


def _handle_status_update(
    notification: Notification,
    user: User,
    zaak: Zaak,
    status: Status,
    status_type_config: ZaakTypeStatusTypeConfig,
    api_group: ZGWApiGroupConfig,
):
    # choose template
    if status_type_config.action_required:
        template_name = "case_status_notification_action_required"
    else:
        template_name = "case_status_notification"

    # hook into userfeed
    hooks.case_status_notification_received(user, zaak, status)

    # email notification
    note = UserCaseStatusNotification.objects.record_if_unique_notification(
        user,
        zaak.uuid,
        status.uuid,
        template_name,
    )
    if not note:
        _log_helper.log_notification_email_duplicate(
            notification, user, status.url, zaak.url
        )
        return

    # let's not spam the users
    period = timedelta(seconds=settings.ZGW_LIMIT_NOTIFICATIONS_FREQUENCY)
    if note.has_received_similar_notes_within(period, template_name):
        _log_helper.log_notification_email_rate_limited(
            notification, user, status.url, zaak.url
        )
        return

    send_case_update_email(
        user, zaak, template_name, api_group=api_group, status=status
    )
    note.mark_sent()

    _log_helper.log_notification_email_sent(notification, user, status.url, zaak.url)


# - - - - -


def _get_np_initiator_bsns_from_roles(
    roles: list[Rol], limit_access_to_role: str = ""
) -> list[str]:
    """
    iterate over Rollen and for all natural-person initiators return their BSN

    If `limit_access_to_role` is set, only roles with that specific omschrijving_generiek
    are included; otherwise both initiator and medeinitiator are included.
    """
    ret = set()
    allowed_rollen = (
        (limit_access_to_role,)
        if limit_access_to_role
        else (RolOmschrijving.initiator, RolOmschrijving.medeinitiator)
    )

    for role in roles:
        if role.omschrijving_generiek not in allowed_rollen:
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


def _get_nnp_initiator_nnp_id_from_roles(
    roles: list[Rol], limit_access_to_role: str = ""
) -> list[str]:
    """
    iterate over Rollen and for all non-natural-person initiators return their nnpId

    If `limit_access_to_role` is set, only roles with that specific omschrijving_generiek
    are included; otherwise both initiator and medeinitiator are included.
    """
    ret = set()
    allowed_rollen = (
        (limit_access_to_role,)
        if limit_access_to_role
        else (RolOmschrijving.initiator, RolOmschrijving.medeinitiator)
    )

    for role in roles:
        if role.omschrijving_generiek not in allowed_rollen:
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


def _get_initiator_users_from_roles(
    roles: list[Rol],
    api_group: ZGWApiGroupConfig,
    limit_access_to_role: str = "",
) -> list[User]:
    """
    iterate over Rollen and return User objects for initiators

    If `limit_access_to_role` is set, only users with that specific role are returned.
    """
    users = []

    bsn_list = _get_np_initiator_bsns_from_roles(
        roles, limit_access_to_role=limit_access_to_role
    )
    if bsn_list:
        users += list(User.objects.filter(bsn__in=bsn_list, is_active=True))

    nnp_id_list = _get_nnp_initiator_nnp_id_from_roles(
        roles, limit_access_to_role=limit_access_to_role
    )
    if nnp_id_list:
        if api_group.fetch_eherkenning_zaken_with_rsin:
            id_filter = {"rsin__in": nnp_id_list}
        else:
            id_filter = {"kvk__in": nnp_id_list}
        users += list(User.objects.filter(is_active=True, **id_filter))

    return users
