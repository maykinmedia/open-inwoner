from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from zgw_consumers.api_models.base import factory

from notifications.api.serializers import NotificatieSerializer
from notifications.constants import ProcessingStatus
from notifications.models import (
    NotificationProcessingConfig,
    NotificationRecord,
)
from open_inwoner.openzaak.api_models import Notification
from open_inwoner.openzaak.auth import get_valid_subscription_from_request
from open_inwoner.openzaak.exceptions import InvalidAuth
from open_inwoner.openzaak.mixins import WebhookLogMixin
from open_inwoner.openzaak.tasks import process_zaken_notification


class NotificationsWebhookBaseView(WebhookLogMixin, APIView):
    """
    Generic ZGW notification webhook handler
    """

    # optionally filter incoming channels
    accept_channels = []

    # disable DRF default auth and permissions
    authentication_classes = []
    permission_classes = []

    parser_classes = [JSONParser]

    def handle_notification(self, notification: NotificationRecord) -> None:
        raise NotImplementedError("extend and override this method")

    def post(self, request):
        # Check payload size before processing
        config = NotificationProcessingConfig.get_solo()
        max_payload_size = config.max_payload_size

        content_length = request.META.get("CONTENT_LENGTH")
        try:
            parsed_content_length = int(content_length) if content_length else None
        except (ValueError, TypeError):
            parsed_content_length = None
        if parsed_content_length is None:
            # No Content-Length (e.g. chunked transfer): buffer and measure.
            # Django caches request._body and resets the stream, so DRF parsing still works.
            parsed_content_length = len(request.body)
        if parsed_content_length > max_payload_size:
            self.log_webhook_payload_too_large(content_length, max_payload_size)
            return Response(
                {"detail": f"payload too large (max {max_payload_size} bytes)"},
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        # find and validate Subscription
        try:
            subscription = get_valid_subscription_from_request(request)
        except InvalidAuth as e:
            self.log_webhook_auth_error(str(e))
            return Response(
                {"detail": "cannot authenticate subscription"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Create initial log, so we have a record if the incoming webhook fails to
        # subsequently process
        try:
            notification_record = NotificationRecord.objects.create(
                subscription=subscription,
                payload=request.data,  # Store as JSON dict
                status=ProcessingStatus.PENDING,
                is_valid=False,
            )
        except ParseError:
            # We don't store invalid JSON
            self.log_webhook_parse_error()
            return Response(
                {"detail": "payload is not valid json"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            self.log_webhook_store_error(e)
            return Response(
                {"detail": "unable to store notification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # deserialize
        serializer = NotificatieSerializer(data=request.data)
        if not serializer.is_valid():
            self.log_webhook_deserialization_error()
            notification_record.status = ProcessingStatus.FAILED
            notification_record.processing_error = (
                f"notification is not valid according to schema: {serializer.errors}"
            )
            notification_record.save(
                update_fields=(
                    "status",
                    "processing_error",
                )
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        notification = factory(Notification, serializer.validated_data)

        # Update record with basic metadata
        notification_record.is_valid = True
        notification_record.kanaal = notification.kanaal
        notification_record.save(
            update_fields=(
                "is_valid",
                "kanaal",
            )
        )

        # Handle test webhooks, and leave a record so it's visible for validation purposes
        if notification.kanaal == "test":
            self.log_webhook_test_channel(notification)

            # Test webhooks don't have to be processed
            notification_record.status = ProcessingStatus.SUCCESS
            notification_record.processing_output = (
                "test channel, no further processing done"
            )
            notification_record.save(
                update_fields=(
                    "status",
                    "processing_output",
                )
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        if notification.kanaal not in subscription.channels:
            self.log_webhook_channel_not_subscribed(notification)

            error_msg = (
                f"notification channel '{notification.kanaal}' not subscribed to"
            )
            notification_record.status = ProcessingStatus.FAILED
            notification_record.processing_error = error_msg
            notification_record.save(
                update_fields=(
                    "status",
                    "processing_error",
                )
            )
            return Response({"detail": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        if self.accept_channels and notification.kanaal not in self.accept_channels:
            self.log_webhook_channel_not_acceptable(notification)

            notification_record.status = ProcessingStatus.FAILED
            notification_record.processing_error = f"notification channel '{notification.kanaal}' not acceptable by webhook"
            notification_record.save(
                update_fields=(
                    "status",
                    "processing_error",
                )
            )
            return Response(
                {
                    "detail": f"notification channel '{notification.kanaal}' not acceptable by webhook"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # call actual handler
        try:
            self.handle_notification(notification_record)
        except Exception as e:
            # handler had an error
            self.log_webhook_handler_error(notification, e)
            notification_record.status = ProcessingStatus.FAILED
            notification_record.processing_error = str(e)
            notification_record.save(update_fields=("status", "processing_error"))
            return Response(
                {"detail": "internal error handling notification"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        else:
            # looks like we're good
            self.log_webhook_notification_received(notification, "accepted")
            return Response(status=status.HTTP_204_NO_CONTENT)


class ZakenNotificationsWebhookView(NotificationsWebhookBaseView):
    accept_channels = [
        "zaken",
    ]

    def handle_notification(self, notification: NotificationRecord):
        process_zaken_notification.delay(notification.pk)
