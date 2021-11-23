from django.urls import include, path

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularRedocView
from rest_framework import routers

from .accounts.views import (
    ActionViewSet,
    AppointmentViewSet,
    ContactViewSet,
    DocumentViewSet,
    GetAuthTokenView,
)
from .configurations.views import SiteConfigurationView
from .pdc.views import CategoryViewSet, ProductViewSet
from .search.views import SearchView

app_name = "api"
router = routers.SimpleRouter()
router.register("actions", ActionViewSet, basename="actions")
router.register("appointments", AppointmentViewSet, basename="appointments")
router.register("contacts", ContactViewSet, basename="contacts")
router.register("categories", CategoryViewSet, basename="categories")
router.register("products", ProductViewSet, basename="products")
router.register("documents", DocumentViewSet, basename="documents")


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
    path("auth/get_token/", GetAuthTokenView.as_view(), name="get_token"),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    # path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("search/", SearchView.as_view(), name="search"),
    path("config/", SiteConfigurationView.as_view(), name="site_configuration"),
    path("", include(router.urls)),
]
