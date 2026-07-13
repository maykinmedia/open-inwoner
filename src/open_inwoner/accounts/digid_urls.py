from django.urls import path

from mozilla_django_oidc.urls import urlpatterns
from mozilla_django_oidc_db.views import OIDCCallbackView

from .views import digid_init, digid_logout

app_name = "digid_oidc"


urlpatterns = [
    # Deprecated: legacy callback URL, kept because customers have whitelisted it in
    # their IdP configuration (see LegacyCallbackURLMixin in oidc_plugins.plugins).
    # Remove in favour of the generic /oidc/callback/ endpoint once IdP whitelists
    # have been updated everywhere.
    path("callback/", OIDCCallbackView.as_view(), name="callback"),
    path("authenticate/", digid_init, name="init"),
    path("logout/", digid_logout, name="logout"),
] + urlpatterns
