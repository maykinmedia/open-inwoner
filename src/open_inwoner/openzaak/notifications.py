from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from functools import partial

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _

import structlog
from mail_editor.helpers import find_template
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
from open_inwoner.openzaak.clients import CatalogiClient, ZakenClient
from open_inwoner.openzaak.documents import fetch_single_information_object_from_url
from open_inwoner.openzaak.mixins import WebhookLogMixin
from open_inwoner.openzaak.models import (
    OpenZaakConfig,
    UserCaseInfoObjectNotification,
    UserCaseStatusNotification,
    ZaakTypeConfig,
    ZaakTypeStatusTypeConfig,
    ZGWApiGroupConfig,
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

logger = structlog.stdlib.get_logger(__name__)

# Create a helper instance for logging
_log_helper = WebhookLogMixin()

# Create log partial for notification drops
log_dropped = partial(logger.info, "Notification dropped")
log_skipped = partial(logger.info, "Notification skipped")


class NotificationStatus(Enum):
    """Status of notification processing."""

    DROPPED = "dropped"
    """Dropped before handling - preliminary checks failed."""

    DISPATCHED_SKIPPED = "dispatched_skipped"
    """Dispatched to handling stage but no emails sent - all users skipped."""

    DISPATCHED_SENT = "dispatched_sent"
    """Dispatched and successfully sent one or more notification emails."""


@dataclass
class NotificationResult:
    """Result of processing a notification."""

    status: NotificationStatus
    """Outcome of notification processing."""

    sent_count: int = 0
    """Number of emails successfully sent (only relevant if status=DISPATCHED_SENT)."""

    reason: str | None = None
    """
    - If DROPPED: why dropped in preliminary stage
    - If DISPATCHED_SKIPPED: why no emails were sent
    - If DISPATCHED_SENT: summary of what was sent/skipped
    """


# TODO: check siteconfig for notification enabled
def handle_zaken_notification(notification: Notification) -> NotificationResult:
    """
    Perform basic checks, then dispatch to
        - `handle_status_notification` or
        - `handle_zaakinformatieobject_notification`
    """
    if notification.kanaal != "zaken":
        reason = f"handler expects kanaal 'zaken' but received '{notification.kanaal}'"
        log_dropped(reason=reason, kanaal=notification.kanaal)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    # on the 'zaken' channel the hoofd_object is always the zaak
    zaak_url = notification.hoofd_object

    # we're only interested in some updates
    resources = ("status", "zaakinformatieobject")
    r = notification.resource  # short alias

    if notification.resource not in resources:
        reason = f"resource is not {_wrap_join(resources, 'or')} but '{notification.resource}'"
        log_dropped(reason=reason, resource=notification.resource, zaak_url=zaak_url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    try:
        api_group = ZGWApiGroupConfig.objects.resolve_group_from_hints(url=zaak_url)
    except ZGWApiGroupConfig.DoesNotExist:
        reason = "no API group defined for zaak"
        log_dropped(reason=reason, zaak_url=zaak_url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    zaken_client = api_group.zaken_client

    # check if we have users that need to be informed about this case
    if not (roles := zaken_client.fetch_zaak_roles(zaak_url)):
        reason = "cannot retrieve rollen for zaak"
        log_dropped(reason=reason, zaak_url=zaak_url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    inform_users = _get_initiator_users_from_roles(roles, api_group=api_group)
    if not inform_users:
        reason = "no users with bsn/nnp_id as (mede)initiators"
        log_dropped(reason=reason, zaak_url=zaak_url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    # check if this case is visible
    if not (zaak := zaken_client.fetch_zaak_by_url_no_cache(zaak_url)):
        reason = "cannot retrieve zaak"
        log_dropped(reason=reason, zaak_url=zaak_url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    zaaktype = api_group.catalogi_client.fetch_single_zaaktype(zaak.zaaktype)

    if not zaaktype:
        reason = f"cannot retrieve zaaktype {zaak.zaaktype}"
        log_dropped(reason=reason, zaak_url=zaak_url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    zaak.zaaktype = zaaktype

    if not is_zaak_visible(zaak):
        reason = "zaak not visible after applying visibility filter"
        log_dropped(reason=reason, zaak_url=zaak_url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    # Dispatch to specific handlers
    match notification.resource:
        case "status":
            return _handle_status_notification(
                notification, zaak, inform_users, api_group
            )
        case "zaakinformatieobject":
            return _handle_zaakinformatieobject_notification(
                notification, zaak, inform_users, api_group
            )
        case _:
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
) -> NotificationResult:
    oz_config = api_group.open_zaak_config

    # check if this is a zaakinformatieobject we want to inform on
    ziobj_url = notification.resource_url

    ziobj = api_group.zaken_client.fetch_single_zaak_information_object(ziobj_url)

    if not ziobj:
        reason = f"cannot retrieve zaakinformatieobject {ziobj_url}"
        log_skipped(reason=reason, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    info_object = fetch_single_information_object_from_url(
        ziobj.informatieobject, api_group=api_group
    )
    if not info_object:
        reason = f"cannot retrieve informatieobject {ziobj.informatieobject}"
        log_skipped(reason=reason, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    ziobj.informatieobject = info_object

    if not is_info_object_visible(info_object, oz_config.document_max_confidentiality):
        reason = "informatieobject not visible after applying visibility filter"
        log_skipped(reason=reason, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    # NOTE for documents we don't check the statustype.informeren
    ztiotc = get_zaak_type_info_object_type_config(
        zaak.zaaktype, info_object.informatieobjecttype
    )
    if not ztiotc:
        reason = f"cannot retrieve info_type configuration {info_object.informatieobjecttype}"
        log_skipped(reason=reason, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)
    elif not ztiotc.document_notification_enabled:
        reason = f"info_type configuration '{ztiotc.omschrijving}' has 'document_notification_enabled' disabled"
        log_skipped(reason=reason, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    # reaching here means we're going to inform users
    _log_helper.log_notification_accepted(notification, inform_users, zaak.url)

    sent_count = 0
    skipped_count = 0
    skip_reasons = []

    for user in inform_users:
        user_result = _handle_zaakinformatieobject_update(
            notification, user, zaak, ziobj, api_group
        )
        if user_result.sent_count > 0:
            sent_count += 1
        else:
            skipped_count += 1
            if user_result.reason and user_result.reason not in skip_reasons:
                skip_reasons.append(user_result.reason)

    if sent_count > 0:
        reason = f"sent {sent_count} email(s)"
        if skipped_count > 0:
            reason += f", skipped {skipped_count} ({', '.join(skip_reasons)})"
        log_system_action(
            f"Sent {sent_count} document notification email(s) for zaak {zaak.url}"
        )
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SENT,
            sent_count=sent_count,
            reason=reason,
        )
    else:
        reason = f"all {len(inform_users)} user(s) skipped: {', '.join(skip_reasons)}"
        logger.info(reason=reason, zaak_url=zaak.url)
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SKIPPED, sent_count=0, reason=reason
        )


def _handle_zaakinformatieobject_update(
    notification: Notification,
    user: User,
    zaak: Zaak,
    zaak_info_object: ZaakInformatieObject,
    api_group: ZGWApiGroupConfig,
) -> NotificationResult:
    template_name = "case_document_notification"

    # hook into userfeed
    hooks.case_document_added_notification_received(user, zaak, zaak_info_object)

    if not user.cases_notifications or not user.get_contact_email():
        _log_helper.log_notification_email_blocked_by_user(
            notification, user, zaak_info_object.url, zaak.url
        )
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SKIPPED,
            sent_count=0,
            reason="user disabled notifications or has no contact email",
        )

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
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SKIPPED,
            sent_count=0,
            reason="duplicate",
        )

    # let's not spam the users
    period = timedelta(seconds=settings.ZGW_LIMIT_NOTIFICATIONS_FREQUENCY)
    if note.has_received_similar_notes_within(period, template_name):
        _log_helper.log_notification_email_rate_limited(
            notification, user, zaak_info_object.url, zaak.url
        )
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SKIPPED,
            sent_count=0,
            reason="rate limited",
        )

    send_case_update_email(user, zaak, template_name, api_group=api_group)
    note.mark_sent()

    _log_helper.log_notification_email_sent(
        notification, user, zaak_info_object.url, zaak.url
    )
    return NotificationResult(status=NotificationStatus.DISPATCHED_SENT, sent_count=1)


#
# Helper functions for status update notifications
#
def _check_status_history(
    notification: Notification, zaak: Zaak, client: ZakenClient
) -> tuple[list[Status] | None, str | None]:
    """
    Check if more than one status exists for `zaak` (else notifications are skipped).

    Returns: (status_history, error_reason) where error_reason is None on success.
    """
    status_history = client.fetch_status_history_no_cache(zaak.url)

    if not status_history:
        return None, "cannot retrieve status_history"

    if len(status_history) == 1:
        return None, "skip initial status notification"

    return status_history, None


def _check_status(
    notification: Notification,
    zaak: Zaak,
    status_history: list[Status],
    client: ZakenClient,
) -> tuple[Status | None, str | None]:
    """
    Check if this is a status we want to inform on.

    Returns: (status, error_reason) where error_reason is None on success.
    """
    status_url = notification.resource_url

    status = None
    for s in status_history:
        if s.url == status_url:
            status = s
            break
    else:
        # TODO currently not covered in tests?
        if client:
            status = client.fetch_single_status(status_url)

    if not status:
        return None, f"cannot retrieve status {status_url}"

    return status, None


def _check_status_type(
    notification: Notification,
    zaak: Zaak,
    status: Status,
    oz_config: OpenZaakConfig,
    catalogi_client: CatalogiClient,
) -> tuple[StatusType | None, str | None]:
    """
    Check if a status_type exists for `status` and if notifications are enabled.

    Returns: (status_type, error_reason) where error_reason is None on success.
    """
    status_type = catalogi_client.fetch_single_status_type(status.statustype)

    if not status_type:
        return None, f"cannot retrieve status_type {status.statustype}"

    if (
        not oz_config.skip_notification_statustype_informeren
        and not status_type.informeren
    ):
        return None, "status_type.informeren is false"

    return status_type, None


def _check_zaaktype_config(
    zaak: Zaak,
    oz_config: OpenZaakConfig,
) -> tuple[ZaakTypeConfig | None, str | None]:
    """
    Check if zaaktype_config exists and notifications are enabled.

    Returns: (zaaktype_config, error_reason) where error_reason is None on success.
    """
    ztc = get_zaak_type_config(zaak.zaaktype)

    if oz_config.skip_notification_statustype_informeren:
        if not ztc:
            zaaktype_id = getattr(zaak.zaaktype, "identificatie", str(zaak.zaaktype))
            return (
                None,
                f"'skip_notification_statustype_informeren' is True but cannot retrieve zaaktype configuration '{zaaktype_id}'",
            )
        elif not ztc.notify_status_changes:
            zaaktype_id = getattr(zaak.zaaktype, "identificatie", str(zaak.zaaktype))
            return (
                None,
                f"zaaktype configuration '{zaaktype_id}' found but 'notify_status_changes' is False",
            )

    return ztc, None


def _check_statustype_config(
    zaak: Zaak,
    ztc: ZaakTypeConfig,
) -> tuple[ZaakTypeStatusTypeConfig | None, str | None]:
    """
    Check if statustype_config exists and notifications are enabled.

    Returns: (statustype_config, error_reason) where error_reason is None on success.
    """
    statustype_url = zaak.status.statustype

    try:
        statustype_config = ZaakTypeStatusTypeConfig.objects.get(
            zaaktype_config=ztc, statustype_url=statustype_url
        )
    except ZaakTypeStatusTypeConfig.DoesNotExist:
        return (
            None,
            f"ZaakTypeStatusTypeConfig could not be found for statustype {statustype_url}",
        )

    if not statustype_config.notify_status_change:
        return None, "'notify_status_change' is False for the status type configuration"

    return statustype_config, None


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
) -> NotificationResult:
    """
    Check status notification settings of user and case-related objects/configs
    """
    oz_config = api_group.open_zaak_config
    catalogi_client = api_group.catalogi_client
    zaken_client = api_group.zaken_client

    status_history, error = _check_status_history(notification, zaak, zaken_client)
    if error:
        log_skipped(reason=error, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=error)

    status, error = _check_status(notification, zaak, status_history, zaken_client)
    if error:
        log_skipped(reason=error, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=error)

    status_type, error = _check_status_type(
        notification, zaak, status, oz_config, catalogi_client
    )
    if error:
        log_skipped(reason=error, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=error)

    ztc, error = _check_zaaktype_config(zaak, oz_config)
    if error:
        log_skipped(reason=error, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=error)

    status = zaken_client.fetch_single_status(zaak.status)
    if not status:
        # TODO: check if should we return or continue if the case has no status
        reason = "Unable to fetch status"
        log_skipped(reason=reason, status_url=zaak.status, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=reason)

    zaak.status = status
    status_type_config, error = _check_statustype_config(zaak, ztc)
    if error:
        log_skipped(reason=error, zaak_url=zaak.url)
        return NotificationResult(status=NotificationStatus.DROPPED, reason=error)

    status.statustype = status_type

    # all checks have passed - now attempt to inform users
    _log_helper.log_notification_accepted(notification, inform_users, zaak.url)

    sent_count = 0
    skipped_count = 0
    skip_reasons = []

    for user in inform_users:
        if not _check_user_status_notitifactions(
            notification, user, zaak, status, status_type_config
        ):
            skipped_count += 1
            reason = "notifications disabled or no contact email"
            if reason not in skip_reasons:
                skip_reasons.append(reason)
            continue

        # TODO: replace with notify_about_status_update(...args, method: Callable)
        user_result = _handle_status_update(
            notification, user, zaak, status, status_type_config, api_group
        )
        if user_result.sent_count > 0:
            sent_count += 1
        else:
            skipped_count += 1
            if user_result.reason and user_result.reason not in skip_reasons:
                skip_reasons.append(user_result.reason)

    if sent_count > 0:
        reason = f"sent {sent_count} email(s)"
        if skipped_count > 0:
            reason += f", skipped {skipped_count} ({', '.join(skip_reasons)})"
        log_system_action(
            f"Sent {sent_count} status notification email(s) for zaak {zaak.url}"
        )
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SENT,
            sent_count=sent_count,
            reason=reason,
        )
    else:
        reason = f"all {len(inform_users)} user(s) skipped: {', '.join(skip_reasons)}"
        logger.info(reason=reason, zaak_url=zaak.url)
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SKIPPED, sent_count=0, reason=reason
        )


def _handle_status_update(
    notification: Notification,
    user: User,
    zaak: Zaak,
    status: Status,
    status_type_config: ZaakTypeStatusTypeConfig,
    api_group: ZGWApiGroupConfig,
) -> NotificationResult:
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
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SKIPPED,
            sent_count=0,
            reason="duplicate",
        )

    # let's not spam the users
    period = timedelta(seconds=settings.ZGW_LIMIT_NOTIFICATIONS_FREQUENCY)
    if note.has_received_similar_notes_within(period, template_name):
        _log_helper.log_notification_email_rate_limited(
            notification, user, status.url, zaak.url
        )
        return NotificationResult(
            status=NotificationStatus.DISPATCHED_SKIPPED,
            sent_count=0,
            reason="rate limited",
        )

    send_case_update_email(
        user, zaak, template_name, api_group=api_group, status=status
    )
    note.mark_sent()

    _log_helper.log_notification_email_sent(notification, user, status.url, zaak.url)
    return NotificationResult(status=NotificationStatus.DISPATCHED_SENT, sent_count=1)


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


def _get_initiator_users_from_roles(
    roles: list[Rol], api_group: ZGWApiGroupConfig
) -> list[User]:
    """
    iterate over Rollen and return User objects for initiators
    """
    users = []

    bsn_list = _get_np_initiator_bsns_from_roles(roles)
    if bsn_list:
        users += list(User.objects.filter(bsn__in=bsn_list, is_active=True))

    nnp_id_list = _get_nnp_initiator_nnp_id_from_roles(roles)
    if nnp_id_list:
        if api_group.fetch_eherkenning_zaken_with_rsin:
            id_filter = {"rsin__in": nnp_id_list}
        else:
            id_filter = {"kvk__in": nnp_id_list}
        users += list(User.objects.filter(is_active=True, **id_filter))

    return users
