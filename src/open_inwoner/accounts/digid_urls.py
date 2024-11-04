from django.urls import path

from mozilla_django_oidc.urls import urlpatterns
from mozilla_django_oidc_db.views import OIDCCallbackView

from .views import digid_init, digid_logout

app_name = "digid_oidc"


urlpatterns = [
    # XXX: generic callback view, this can move to a single URL.
    path("callback/", OIDCCallbackView.as_view(), name="callback"),
    path("authenticate/", digid_init, name="init"),
    path("logout/", digid_logout, name="logout"),
] + urlpatterns
