from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import (
    DigiDOIDCAuthenticationCallbackView,
    DigiDOIDCAuthenticationRequestView,
    DigiDOIDCLogoutView,
)

app_name = "digid_oidc"


urlpatterns = [
    path(
        "callback/",
        DigiDOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
    path(
        "authenticate/",
        DigiDOIDCAuthenticationRequestView.as_view(),
        name="init",
    ),
    path(
        "logout/",
        DigiDOIDCLogoutView.as_view(),
        name="logout",
    ),
] + urlpatterns
