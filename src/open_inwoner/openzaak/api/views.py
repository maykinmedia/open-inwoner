import logging

from notifications_api_common.api.serializers import NotificatieSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from zgw_consumers.api_models.base import factory

from open_inwoner.openzaak.api_models import Notification
from open_inwoner.openzaak.exceptions import NotificationNotAcceptable
from open_inwoner.openzaak.notifications import handle_notification

logger = logging.getLogger(__name__)


class NotificationsWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    accept_channels = [
        "zaken",
    ]

    def handle_notification(self, notification: Notification):
        if self.accept_channels and notification.kanaal not in self.accept_channels:
            raise NotificationNotAcceptable(
                f"kanaal '{notification.kanaal}' not accepted"
            )

        handle_notification(notification)

    # TODO add Authorization header verification
    def post(self, request):
        serializer = NotificatieSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error("received invalid notification")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        notification = factory(Notification, serializer.validated_data)
        try:
            self.handle_notification(notification)
        except NotificationNotAcceptable as e:
            logger.exception(f"notification not acceptable: {e}", exc_info=e)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
