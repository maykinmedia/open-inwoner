import logging  # noqa: TID251 - only used for log levels
from typing import TYPE_CHECKING

from django.http import HttpRequest

import structlog

from open_inwoner.openzaak.metrics import (
    webhook_notification_emails_sent,
    webhook_notifications_processed,
    webhook_notifications_received,
    webhook_processing_failures,
    webhook_processing_skipped,
)
from open_inwoner.utils.logentry import system_action as log_system_action
from open_inwoner.utils.views import LogMixin

if TYPE_CHECKING:
    from open_inwoner.openzaak.api_models import Notification

logger = structlog.get_logger(__name__)


class WebhookLogMixin(LogMixin):
    """Mixin for logging and metrics related to webhook notifications"""

    request: HttpRequest

    def log_webhook_notification_received(
        self, notification: "Notification", result: str
    ):
        webhook_notifications_received.add(
            1, {"channel": notification.kanaal, "result": result}
        )

    def log_webhook_auth_error(self, error_message: str):
        logger.warning("webhook auth error", error=error_message)
        webhook_processing_failures.add(
            1, {"channel": "unknown", "reason": "auth_error"}
        )

    def log_webhook_deserialization_error(self):
        logger.warning("cannot deserialize notification")
        webhook_processing_failures.add(
            1, {"channel": "unknown", "reason": "deserialization_error"}
        )

    def log_webhook_test_channel(self, notification: "Notification"):
        log_system_action(
            "received notification on 'test' channel", log_level=logging.INFO
        )
        self.log_webhook_notification_received(notification, result="accepted")

    def log_webhook_channel_not_subscribed(self, notification: "Notification"):
        msg = f"notification channel '{notification.kanaal}' not subscribed to"
        log_system_action(msg, log_level=logging.ERROR)
        self.log_webhook_notification_received(notification, result="not_subscribed")

    def log_webhook_channel_not_acceptable(self, notification: "Notification"):
        msg = f"notification channel '{notification.kanaal}' not acceptable by webhook"
        log_system_action(msg, log_level=logging.ERROR)
        self.log_webhook_notification_received(notification, result="not_acceptable")

    def log_webhook_parse_error(self):
        logger.warning("cannot store notification: payload is not valid JSON")
        webhook_processing_failures.add(
            1, {"channel": "unknown", "reason": "parse_error"}
        )

    def log_webhook_store_error(self, error: Exception):
        logger.warning("cannot store notification", error=str(error))
        webhook_processing_failures.add(
            1, {"channel": "unknown", "reason": "store_error"}
        )

    def log_webhook_handler_error(self, notification: "Notification", error: Exception):
        logger.warning(
            "error handling notification",
            channel=notification.kanaal,
            error=str(error),
        )
        self.log_webhook_notification_received(notification, result="handler_error")

    def log_notification_ignored(
        self,
        notification: "Notification",
        reason: str,
        case_url: str,
    ):
        logger.warning(
            "ignored notification",
            resource=notification.resource,
            reason=reason,
            case_url=case_url,
        )
        webhook_processing_skipped.add(
            1, {"channel": notification.kanaal, "reason": reason}
        )

    def log_webhook_payload_too_large(
        self, content_length: str | None, max_payload_size: int
    ):
        logger.warning(
            "rejected webhook: payload too large",
            content_length=content_length,
            max_size=max_payload_size,
        )
        webhook_processing_failures.add(
            1, {"channel": "unknown", "reason": "payload_too_large"}
        )

    def log_notification_accepted(
        self, notification: "Notification", users: list, case_url: str
    ):
        from open_inwoner.openzaak.notifications import _wrap_join

        log_system_action(
            f"accepted {notification.resource} notification: attempt informing users {_wrap_join(users)} for case {case_url}",
            log_level=logging.INFO,
        )
        webhook_notifications_processed.add(
            1, {"channel": notification.kanaal, "resource": notification.resource}
        )

    def log_notification_email_blocked_by_user(
        self, notification: "Notification", user, resource_url: str, case_url: str
    ):
        log_system_action(
            f"ignored user-disabled notification delivery for user '{user}' {resource_url} case {case_url}",
            log_level=logging.INFO,
        )

    def log_notification_email_duplicate(
        self, notification: "Notification", user, resource_url: str, case_url: str
    ):
        log_system_action(
            f"ignored duplicate {notification.resource} notification delivery for user '{user}' {resource_url} case {case_url}",
            log_level=logging.INFO,
        )

    def log_notification_email_rate_limited(
        self, notification: "Notification", user, resource_url: str, case_url: str
    ):
        log_system_action(
            f"blocked over-frequent {notification.resource} notification email for user '{user}' {resource_url} case {case_url}",
            log_level=logging.INFO,
        )

    def log_notification_email_sent(
        self,
        notification: "Notification",
        user,
        resource_url: str,
        case_url: str,
        template_name: str = "",
    ):
        log_system_action(
            f"sent {notification.resource} notification email for user '{user}' {resource_url} case {case_url}",
            log_level=logging.INFO,
        )
        webhook_notification_emails_sent.add(
            1,
            {
                "notification_type": notification.resource,
                "template_name": template_name,
            },
        )
