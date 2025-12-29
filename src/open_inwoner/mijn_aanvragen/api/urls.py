from django.urls import path

from open_inwoner.mijn_aanvragen.api.views import ZakenNotificationsWebhookView

app_name = "openzaak"

urlpatterns = [
    path(
        "notifications/webhook/zaken",
        ZakenNotificationsWebhookView.as_view(),
        name="notifications_webhook_zaken",
    ),
]
