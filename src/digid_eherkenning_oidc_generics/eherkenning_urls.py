from django.urls import path

from mozilla_django_oidc.urls import urlpatterns

from .views import (
    eherkenning_init,
    eHerkenningOIDCAuthenticationCallbackView,
    eHerkenningOIDCLogoutView,
)

app_name = "eherkenning_oidc"


urlpatterns = [
    path(
        "callback/",
        eHerkenningOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
    path("authenticate/", eherkenning_init, name="init"),
    path(
        "logout/",
        eHerkenningOIDCLogoutView.as_view(),
        name="logout",
    ),
] + urlpatterns
