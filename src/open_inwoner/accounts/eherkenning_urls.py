from django.urls import path

from digid_eherkenning_oidc_generics.eherkenning_urls import urlpatterns

from .views import CustomEHerkenningOIDCAuthenticationCallbackView

app_name = "eherkenning_oidc"


urlpatterns = [
    path(
        "callback/",
        CustomEHerkenningOIDCAuthenticationCallbackView.as_view(),
        name="callback",
    ),
] + urlpatterns
