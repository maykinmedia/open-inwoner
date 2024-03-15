import logging

from notifications_api_common.models import Subscription

from open_inwoner.openklant.notifications import handle_contactmomenten_notification
from open_inwoner.openzaak.api.views import NotificationsWebhookBaseView
from open_inwoner.openzaak.api_models import Notification

logger = logging.getLogger(__name__)


class ContactmomentenNotificationsWebhookView(NotificationsWebhookBaseView):
    accept_channels = [
        "zaken",
    ]

    def handle_notification(
        self, subscription: Subscription, notification: Notification
    ):
        handle_contactmomenten_notification(notification)
