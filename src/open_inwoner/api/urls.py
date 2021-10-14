from django.urls import include, path

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularRedocView

app_name = "api"
urlpatterns = [
    path(
        "schema/",
        SpectacularJSONAPIView.as_view(authentication_classes=[]),
        name="schema",
    ),
    path(
        "docs/",
        SpectacularRedocView.as_view(authentication_classes=[], url_name="api:schema"),
        name="docs",
    ),
    path("contacts/", include("open_inwoner.api.contacts.urls")),
]
