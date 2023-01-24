import logging

from notifications_api_common.api.serializers import NotificatieSerializer
from notifications_api_common.models import Subscription
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from zgw_consumers.api_models.base import factory

from open_inwoner.openzaak.api_models import Notification
from open_inwoner.openzaak.auth import get_valid_subscription_from_request
from open_inwoner.openzaak.exceptions import InvalidAuth
from open_inwoner.openzaak.notifications import handle_zaken_notification
from open_inwoner.utils.logentry import system_action as log_system_action

logger = logging.getLogger(__name__)


class NotificationsWebhookBaseView(APIView):
    """
    generic ZGW notification webhook handler

    theoretically this could be moved to notifications-api-common
    """

    # optionally filter incoming channels
    accept_channels = []

    # disable DRF default auth and permissions
    authentication_classes = []
    permission_classes = []

    def handle_notification(
        self, subscription: Subscription, notification: Notification
    ) -> None:
        raise NotImplementedError("extend and override this method")

    def post(self, request):
        # find and validate Subscription
        try:
            subscription = get_valid_subscription_from_request(request)
        except InvalidAuth as e:
            log_system_action(str(e), log_level=logging.ERROR)
            return Response(
                {"detail": "cannot authenticate subscription"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # deserialize
        serializer = NotificatieSerializer(data=request.data)
        if not serializer.is_valid():
            log_system_action(
                "cannot deserialize notification", log_level=logging.ERROR
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        notification = factory(Notification, serializer.validated_data)

        # verify channel
        if notification.kanaal not in subscription.channels:
            msg = f"notification channel '{notification.kanaal}' not subscribed to"
            log_system_action(msg, log_level=logging.ERROR)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        if self.accept_channels and notification.kanaal not in self.accept_channels:
            msg = f"notification channel '{notification.kanaal}' not acceptable by webhook"
            log_system_action(msg, log_level=logging.ERROR)
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)

        # call actual handler
        try:
            self.handle_notification(subscription, notification)
        except Exception as e:
            # handler had an error
            log_system_action(
                f"error handling notification: {e}", log_level=logging.ERROR, exc_info=e
            )
            return Response(
                {"detail": "internal error handling notification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        else:
            log_system_action(f"handled notification", log_level=logging.DEBUG)
            # looks like we're good
            return Response(status=status.HTTP_204_NO_CONTENT)


class ZakenNotificationsWebhookView(NotificationsWebhookBaseView):
    accept_channels = [
        "zaken",
    ]

    def handle_notification(
        self, subscription: Subscription, notification: Notification
    ):
        handle_zaken_notification(notification)
