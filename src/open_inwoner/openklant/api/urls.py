from django.urls import path

from open_inwoner.openklant.api.views import ContactmomentenNotificationsWebhookView

app_name = "openklant"

urlpatterns = [
    path(
        "notifications/webhook/contactmomenten",
        ContactmomentenNotificationsWebhookView.as_view(),
        name="notifications_webhook_contactmomenten",
    ),
]
