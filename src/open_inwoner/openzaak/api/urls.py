from django.urls import path

from open_inwoner.openzaak.api.views import NotificationsWebhookView

app_name = "openzaak"

urlpatterns = [
    path(
        "notifications/webhook/",
        NotificationsWebhookView.as_view(),
        name="notifications-webhook",
    ),
]
