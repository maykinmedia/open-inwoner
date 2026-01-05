from opentelemetry import metrics

meter = metrics.get_meter("open_inwoner.openzaak")

webhook_notifications_received = meter.create_counter(
    "oip.webhooks.notifications_received",
    unit="{notification}",
    description=(
        "Number of webhook notifications received. "
        "Attributes: channel (str), result (str)"
    ),
)

webhook_notifications_processed = meter.create_counter(
    "oip.webhooks.notifications_processed",
    unit="{notification}",
    description=(
        "Number of webhook notifications successfully processed. "
        "Attributes: channel (str), resource (str)"
    ),
)

webhook_notification_emails_sent = meter.create_counter(
    "oip.webhooks.notification_emails_sent",
    unit="{email}",
    description=(
        "Number of notification emails sent to users. "
        "Attributes: notification_type (str), template_name (str)"
    ),
)
