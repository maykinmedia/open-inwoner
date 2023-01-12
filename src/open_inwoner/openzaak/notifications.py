from open_inwoner.openzaak.api_models import Notification
from open_inwoner.openzaak.exceptions import NotificationNotAcceptable


def handle_notification(notification: Notification):
    if notification.resource == "zaak":
        handle_zaak(notification)
    else:
        raise NotificationNotAcceptable(
            f"resource not mapped '{notification.resource}'"
        )


def handle_zaak(notification: Notification):
    pass
