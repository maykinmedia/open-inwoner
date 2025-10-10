from opentelemetry import metrics

meter = metrics.get_meter("open_inwoner.openzaak")

webhook_notifications_received = meter.create_counter(
    "webhooks.notifications_received",
    unit="1",
    description=(
        "Number of webhook notifications received. "
        "Attributes: channel (str), result (str)"
    ),
)

webhook_notifications_processed = meter.create_counter(
    "webhooks.notifications_processed",
    unit="1",
    description=(
        "Number of webhook notifications successfully processed. "
        "Attributes: channel (str), resource (str)"
    ),
)

webhook_notification_emails_sent = meter.create_counter(
    "webhooks.notification_emails_sent",
    unit="1",
    description=(
        "Number of notification emails sent to users. "
        "Attributes: notification_type (str), template_name (str)"
    ),
)
