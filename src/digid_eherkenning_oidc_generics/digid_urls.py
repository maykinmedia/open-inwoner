from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import DigiDOIDCAuthenticationCallbackView, DigiDOIDCLogoutView, digid_init

app_name = "digid_oidc"


urlpatterns = [
    path(
        "callback/",
        DigiDOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
    path("authenticate/", digid_init, name="init"),
    path(
        "logout/",
        DigiDOIDCLogoutView.as_view(),
        name="logout",
    ),
] + urlpatterns
