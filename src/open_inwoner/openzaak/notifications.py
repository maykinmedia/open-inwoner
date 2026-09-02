import enum
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Generic, TypeVar

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
)
from open_inwoner.userfeed import hooks
from open_inwoner.utils.url import build_absolute_url

logger = structlog.stdlib.get_logger(__name__)

# Create a helper instance for logging
_log_helper = WebhookLogMixin()


T = TypeVar("T")


class NotificationOutcome(enum.Enum):
    """Whether a notification-processing step was ignored or went ahead"""

    IGNORED = "ignored"
    PROCESSED = "processed"


@dataclass(frozen=True)
class NotificationProcessingResult(Generic[T]):
    """
    Outcome of (a step in) handling a notification.

    `outcome` dictates control flow at the caller: `IGNORED` means the caller
    should stop and report `message` (why it was ignored); `PROCESSED` means
    `value` holds whatever was checked/produced, and the caller should
    continue using it.

    `str()` renders `message` plus optional structured `context` as a single
    human-readable line - this is what callers (e.g. the
    `process_zaken_notification` task) store on the NotificationRecord as
    `processing_output`.
    """

    outcome: NotificationOutcome
    message: str
    value: T | None = None
    level: str = "info"
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def ignored(self) -> bool:
        return self.outcome is NotificationOutcome.IGNORED

    def __str__(self) -> str:
        if not self.context:
            return self.message
        detail = ", ".join(f"{k}={v}" for k, v in self.context.items())
        return f"{self.message} ({detail})"

    @classmethod
    def ignore(
        cls, message: str, *, level: str = "info", **context
    ) -> "NotificationProcessingResult":
        """
        Log `message` (with structured `context`) at `level`, then return it as
        a result explaining why the notification was ignored.
        """
        getattr(logger, level)(message, **context)
        return cls(NotificationOutcome.IGNORED, message, level=level, context=context)

    @classmethod
    def ok(cls, value: T) -> "NotificationProcessingResult[T]":
        """
        Continue processing with `value` - nothing to report, so nothing is logged.
        """
        return cls(NotificationOutcome.PROCESSED, "", value=value)

    @classmethod
    def processed(cls, message: str, **context) -> "NotificationProcessingResult":
        """
        Log `message` (with structured `context`), then return it as a result
        summarizing what was done.
        """
        logger.info(message, **context)
        return cls(NotificationOutcome.PROCESSED, message, context=context)


def handle_zaken_notification(
    notification: Notification,
) -> NotificationProcessingResult:
    """
    Perform basic checks, then dispatch to
        - `handle_status_notification` or
        - `handle_zaakinformatieobject_notification`

    Returns a `NotificationProcessingResult` describing the outcome: why the
    notification was ignored, or a short summary of what was done. Callers
    (e.g. the `process_zaken_notification` task) format this and store it on
    the NotificationRecord as `processing_output`.
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
        return NotificationProcessingResult.ignore(
            "ignored notification: resource is not one of the expected resources",
            resource=r,
            expected_resources=resources,
            zaak_url=zaak_url,
        )

    try:
        api_group = ZGWApiGroupConfig.objects.resolve_group_from_hints(url=zaak_url)
    except ZGWApiGroupConfig.DoesNotExist:
        return NotificationProcessingResult.ignore(
            "ignored notification: no API group configured for zaak",
            level="error",
            zaak_url=zaak_url,
        )

    service = ZGWService(use_cache=False)

    # check if we have users that need to be informed about this case
    try:
        roles = service.fetch_zaak_roles(zaak_url, api_group)
    except (ZgwAPIError, RequestException):
        # NOTE this used to be logger.error, but as this is also our first call
        # we get a lot of 403 "Niet geautoriseerd voor zaaktype"
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve rollen for zaak",
            resource=r,
            zaak_url=zaak_url,
        )

    config = OpenZaakConfig.get_solo()
    inform_users = _get_initiator_users_from_roles(
        roles,
        api_group=api_group,
        limit_access_to_role=config.limit_user_visible_cases_to_role,
    )
    if not inform_users:
        return NotificationProcessingResult.ignore(
            "ignored notification: no users with bsn/nnp_id as (mede)initiators in zaak",
            resource=r,
            zaak_url=zaak_url,
        )

    # check if this case is visible
    try:
        zaak = service.fetch_zaak_by_url(zaak_url, api_group)
    except (ZgwAPIError, RequestException):
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve zaak",
            level="error",
            resource=r,
            zaak_url=zaak_url,
        )

    zaaktype_url = zaak.zaaktype  # URL string before resolution
    try:
        zaaktype = service.fetch_zaaktype_by_url(zaaktype_url, api_group)
    except (ZgwAPIError, RequestException):
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve zaaktype",
            level="error",
            resource=r,
            zaaktype_url=zaaktype_url,
        )
    zaak.zaaktype = zaaktype

    if not service._is_zaak_visible(zaak)[0]:
        return NotificationProcessingResult.ignore(
            "ignored notification: zaak not visible after applying website visibility filter",
            resource=r,
            zaak_url=zaak_url,
        )

    if notification.resource == "status":
        return _handle_status_notification(
            notification, zaak, inform_users, api_group, service
        )
    elif notification.resource == "zaakinformatieobject":
        return _handle_zaakinformatieobject_notification(
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
        "zaak_identificatie_label": config.zaak_identificatie_label,
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
) -> NotificationProcessingResult:
    oz_config = api_group.open_zaak_config
    r = notification.resource  # short alias for logging

    # check if this is a zaakinformatieobject we want to inform on
    ziobj_url = notification.resource_url
    service = ZGWService(use_cache=False)

    try:
        ziobj = service.fetch_single_zaak_information_object(ziobj_url, api_group)
    except (ZgwAPIError, RequestException):
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve zaakinformatieobject",
            level="error",
            resource=r,
            ziobj_url=ziobj_url,
            zaak_url=zaak.url,
        )

    try:
        info_object = service.fetch_information_object_by_url(
            ziobj.informatieobject, api_group
        )
    except ZgwAPIError:
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve informatieobject",
            level="error",
            resource=r,
            informatieobject_url=ziobj.informatieobject,
            zaak_url=zaak.url,
        )

    ziobj.informatieobject = info_object

    if not service._is_info_object_visible(
        info_object,
        oz_config.document_max_confidentiality,
        oz_config.document_visible_statuses,
    ):
        return NotificationProcessingResult.ignore(
            "ignored notification: informatieobject not visible after applying "
            "website visibility filter",
            resource=r,
            zaak_url=zaak.url,
        )

    # NOTE for documents we don't check the statustype.informeren
    ztiotc = get_zaak_type_info_object_type_config(
        zaak.zaaktype, info_object.informatieobjecttype
    )
    if not ztiotc:
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve info_type configuration",
            resource=r,
            informatieobjecttype=info_object.informatieobjecttype,
            zaak_url=zaak.url,
        )
    elif not ztiotc.document_notification_enabled:
        return NotificationProcessingResult.ignore(
            "ignored notification: info_type configuration found but "
            "'document_notification_enabled' is False",
            resource=r,
            info_type_omschrijving=ztiotc.omschrijving,
            informatieobjecttype=info_object.informatieobjecttype,
            zaak_url=zaak.url,
        )

    # reaching here means we're going to inform users
    _log_helper.log_notification_accepted(notification, inform_users, zaak.url)
    emailed = 0
    for user in inform_users:
        if _handle_zaakinformatieobject_update(
            notification, user, zaak, ziobj, api_group
        ):
            emailed += 1

    return NotificationProcessingResult.processed(
        "processed zaakinformatieobject notification for zaak",
        zaak_url=zaak.url,
        informed_users=len(inform_users),
        emailed_users=emailed,
    )


def _handle_zaakinformatieobject_update(
    notification: Notification,
    user: User,
    zaak: Zaak,
    zaak_info_object: ZaakInformatieObject,
    api_group: ZGWApiGroupConfig,
) -> bool:
    """
    Inform one user about a document. Returns whether an email was sent, so the
    caller can report how many users were actually reached.
    """
    template_name = "case_document_notification"

    # hook into userfeed
    hooks.case_document_added_notification_received(user, zaak, zaak_info_object)

    if not user.cases_notifications or not user.get_contact_email():
        _log_helper.log_notification_email_blocked_by_user(
            notification, user, zaak_info_object.url, zaak.url
        )
        return False

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
        return False

    # let's not spam the users
    period = timedelta(seconds=OpenZaakConfig.get_solo().notification_frequency_limit)
    if note.has_received_similar_notes_within(period, template_name):
        _log_helper.log_notification_email_rate_limited(
            notification, user, zaak_info_object.url, zaak.url
        )
        return False

    send_case_update_email(user, zaak, template_name, api_group=api_group)
    note.mark_sent()

    _log_helper.log_notification_email_sent(
        notification, user, zaak_info_object.url, zaak.url, template_name=template_name
    )
    return True


#
# Helper functions for status update notifications
#
def _check_status_history(
    notification: Notification,
    zaak: Zaak,
    service: ZGWService,
    api_group: ZGWApiGroupConfig,
) -> NotificationProcessingResult[list[Status]]:
    """
    Check if more than one status exists for `zaak` (else notifications are skipped)
    """
    resource = notification.resource
    try:
        status_history = service.fetch_status_history(zaak.url, api_group)
    except (ZgwAPIError, RequestException):
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve status_history for zaak",
            level="error",
            resource=resource,
            zaak_url=zaak.url,
        )

    if not status_history:
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve status_history for zaak",
            level="error",
            resource=resource,
            zaak_url=zaak.url,
        )

    if len(status_history) == 1:
        return NotificationProcessingResult.ignore(
            "ignored notification: skip initial status notification for zaak",
            resource=resource,
            zaak_url=zaak.url,
        )

    return NotificationProcessingResult.ok(status_history)


def _check_status(
    notification: Notification,
    zaak: Zaak,
    status_history: list[Status],
    service: ZGWService,
    api_group: ZGWApiGroupConfig,
) -> NotificationProcessingResult[Status]:
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
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve status for zaak",
            level="error",
            resource=resource,
            status_url=status_url,
            zaak_url=zaak.url,
        )

    return NotificationProcessingResult.ok(status)


def _check_status_type(
    notification: Notification,
    zaak: Zaak,
    status: Status,
    oz_config: OpenZaakConfig,
    service: ZGWService,
    api_group: ZGWApiGroupConfig,
) -> NotificationProcessingResult[StatusType]:
    """
    Check if a status_type exists for `status` and if notifications are enabled
    """
    resource = notification.resource

    try:
        status_type = service.fetch_single_status_type(status.statustype, api_group)
    except (ZgwAPIError, RequestException):
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve status_type for zaak",
            level="error",
            resource=resource,
            statustype_url=status.statustype,
            zaak_url=zaak.url,
        )

    if (
        not oz_config.skip_notification_statustype_informeren
        and not status_type.informeren
    ):
        return NotificationProcessingResult.ignore(
            "ignored notification: status_type.informeren is false for status and zaak",
            resource=resource,
            status_url=status.url,
            zaak_url=zaak.url,
        )

    return NotificationProcessingResult.ok(status_type)


def _check_zaaktype_config(
    notification: Notification,
    zaak: Zaak,
    oz_config: OpenZaakConfig,
) -> NotificationProcessingResult[ZaakTypeConfig]:
    """
    Check if zaaktype_config exists and notifications are enabled
    """
    resource = notification.resource
    ztc = get_zaak_type_config(zaak.zaaktype)

    if oz_config.skip_notification_statustype_informeren:
        if not ztc:
            return NotificationProcessingResult.ignore(
                "ignored notification: 'skip_notification_statustype_informeren' "
                "is True but cannot retrieve zaaktype configuration for zaak",
                resource=resource,
                zaaktype_identificatie=zaak.zaaktype.identificatie,
                zaak_url=zaak.url,
            )
        elif not ztc.notify_status_changes:
            return NotificationProcessingResult.ignore(
                "ignored notification: zaaktype configuration found but "
                "'notify_status_changes' is False",
                resource=resource,
                zaaktype_identificatie=zaak.zaaktype.identificatie,
                zaak_url=zaak.url,
            )
    elif not ztc:
        return NotificationProcessingResult.ignore(
            "ignored notification: cannot retrieve zaaktype configuration for zaak",
            resource=resource,
            zaak_url=zaak.url,
        )

    return NotificationProcessingResult.ok(ztc)


def _check_statustype_config(
    notification: Notification,
    zaak: Zaak,
    ztc: ZaakTypeConfig,
) -> NotificationProcessingResult[ZaakTypeStatusTypeConfig]:
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
        return NotificationProcessingResult.ignore(
            "ignored notification: ZaakTypeStatusTypeConfig could not be found for statustype",
            resource=resource,
            statustype_url=statustype_url,
        )

    if not statustype_config.notify_status_change:
        return NotificationProcessingResult.ignore(
            "ignored notification: 'notify_status_change' is False for the status "
            "type configuration of the status of this zaak",
            resource=resource,
            zaak_url=zaak.url,
        )

    return NotificationProcessingResult.ok(statustype_config)


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
) -> NotificationProcessingResult:
    """
    Check status notification settings of user and case-related objects/configs
    """
    oz_config = api_group.open_zaak_config

    result = _check_status_history(notification, zaak, service, api_group)
    if result.ignored:
        return result
    status_history = result.value

    result = _check_status(notification, zaak, status_history, service, api_group)
    if result.ignored:
        return result
    status = result.value

    result = _check_status_type(
        notification, zaak, status, oz_config, service, api_group
    )
    if result.ignored:
        return result
    status_type = result.value

    result = _check_zaaktype_config(notification, zaak, oz_config)
    if result.ignored:
        return result
    ztc = result.value

    status = service.fetch_single_status(zaak.status, api_group)
    if not status:
        # TODO: check if should we return or continue if the case has no status
        return NotificationProcessingResult.ignore(
            "ignored notification: unable to fetch status for zaak",
            level="error",
            resource=notification.resource,
            status_url=zaak.status,
            zaak_url=zaak.url,
        )

    zaak.status = status
    result = _check_statustype_config(notification, zaak, ztc)
    if result.ignored:
        return result
    status_type_config = result.value

    status.statustype = status_type

    emailed = 0
    for user in inform_users:
        if not _check_user_status_notitifactions(
            notification, user, zaak, status, status_type_config
        ):
            return NotificationProcessingResult.ignore(
                "ignored notification: user has case notifications disabled or "
                "no contact email for zaak",
                resource=notification.resource,
                user=str(user),
                zaak_url=zaak.url,
            )

        # all checks have passed
        _log_helper.log_notification_accepted(notification, inform_users, zaak.url)
        # TODO: replace with notify_about_status_update(...args, method: Callable)
        if _handle_status_update(
            notification, user, zaak, status, status_type_config, api_group
        ):
            emailed += 1

    return NotificationProcessingResult.processed(
        "processed status notification for zaak",
        zaak_url=zaak.url,
        informed_users=len(inform_users),
        emailed_users=emailed,
    )


def _handle_status_update(
    notification: Notification,
    user: User,
    zaak: Zaak,
    status: Status,
    status_type_config: ZaakTypeStatusTypeConfig,
    api_group: ZGWApiGroupConfig,
) -> bool:
    """
    Inform one user about a status change. Returns whether an email was sent,
    so the caller can report how many users were actually reached.
    """
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
        return False

    # let's not spam the users
    period = timedelta(seconds=OpenZaakConfig.get_solo().notification_frequency_limit)
    if note.has_received_similar_notes_within(period, template_name):
        _log_helper.log_notification_email_rate_limited(
            notification, user, status.url, zaak.url
        )
        return False

    send_case_update_email(
        user, zaak, template_name, api_group=api_group, status=status
    )
    note.mark_sent()

    _log_helper.log_notification_email_sent(
        notification, user, status.url, zaak.url, template_name=template_name
    )
    return True


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
