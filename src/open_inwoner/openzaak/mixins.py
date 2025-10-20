import logging  # noqa: TID251 - only used for log levels
from typing import TYPE_CHECKING

from django.http import HttpRequest

from open_inwoner.openzaak.metrics import (
    webhook_notification_emails_sent,
    webhook_notifications_processed,
    webhook_notifications_received,
)
from open_inwoner.utils.logentry import system_action as log_system_action
from open_inwoner.utils.views import LogMixin

if TYPE_CHECKING:
    from open_inwoner.openzaak.api_models import Notification


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
        log_system_action(error_message, log_level=logging.ERROR)

    def log_webhook_deserialization_error(self):
        log_system_action("cannot deserialize notification", log_level=logging.ERROR)

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

    def log_webhook_handler_error(self, notification: "Notification", error: Exception):
        log_system_action(
            f"error handling notification: {error}",
            log_level=logging.ERROR,
            exc_info=error,
        )
        self.log_webhook_notification_received(notification, result="handler_error")

    def log_notification_ignored(
        self,
        notification: "Notification",
        reason: str,
        case_url: str,
        log_level: int = logging.INFO,
    ):
        log_system_action(
            f"ignored {notification.resource} notification: {reason} for case {case_url}",
            log_level=log_level,
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
    ):
        log_system_action(
            f"sent {notification.resource} notification email for user '{user}' {resource_url} case {case_url}",
            log_level=logging.INFO,
        )
        webhook_notification_emails_sent.add(
            1,
            {
                "notification_type": notification.resource,
            },
        )
