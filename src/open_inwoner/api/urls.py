from django.urls import include, path

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularRedocView
from rest_framework import routers

from open_inwoner.reporting_api.views import reporting_api_view

from .pdc.views import CategoryViewSet, ProductViewSet
from .search.views import AutocompleteView

app_name = "api"
router = routers.SimpleRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("products", ProductViewSet, basename="products")


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
    path(
        "reporting-api/",
        reporting_api_view,
        name="reporting_api",
    ),
    path("", include(router.urls)),
]
