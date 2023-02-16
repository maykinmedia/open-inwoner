from django.urls import path

from open_inwoner.openzaak.api.views import ZakenNotificationsWebhookView

app_name = "openzaak"

urlpatterns = [
    path(
        "notifications/webhook/zaken",
        ZakenNotificationsWebhookView.as_view(),
        name="notifications_webhook_zaken",
    ),
]
