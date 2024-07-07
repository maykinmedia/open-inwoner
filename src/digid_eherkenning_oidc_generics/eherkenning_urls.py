from django.urls import path

from mozilla_django_oidc.urls import urlpatterns
from mozilla_django_oidc_db.views import OIDCCallbackView

from .views import eherkenning_init, eHerkenningOIDCLogoutView

app_name = "eherkenning_oidc"


urlpatterns = [
    # XXX: generic callback view, this can move to a single URL.
    path("callback/", OIDCCallbackView.as_view(), name="callback"),
    path("authenticate/", eherkenning_init, name="init"),
    path("logout/", eHerkenningOIDCLogoutView.as_view(), name="logout"),
] + urlpatterns
