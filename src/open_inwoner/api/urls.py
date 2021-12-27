from django.urls import include, path

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularRedocView
from rest_framework import routers

from .search.views import AutocompleteView

app_name = "api"
router = routers.SimpleRouter()


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
    path(
        "search/autocomplete/", AutocompleteView.as_view(), name="search_autocomplete"
    ),
    path("", include(router.urls)),
]
