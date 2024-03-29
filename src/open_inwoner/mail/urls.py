from django.urls import path

from open_inwoner.mail.views import EmailVerificationTokenView

app_name = "mail"


urlpatterns = [
    path(
        "verification/",
        EmailVerificationTokenView.as_view(),
        name="verification",
    ),
]
