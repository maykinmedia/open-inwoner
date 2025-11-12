from django.urls import path

from mozilla_django_oidc.urls import urlpatterns
from mozilla_django_oidc_db.views import OIDCCallbackView

from .views import eidas_init, eidas_logout

app_name = "eidas_oidc"


urlpatterns = [
    path("callback/", OIDCCallbackView.as_view(), name="callback"),
    path("authenticate/", eidas_init, name="init"),
    path("logout/", eidas_logout, name="logout"),
] + urlpatterns
