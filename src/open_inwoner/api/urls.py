from django.urls import include, path

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularRedocView
from rest_framework import routers

from .accounts.views import GetAuthTokenView
from .contacts.views import ContactViewSet
from .pdc.views import CategoryViewSet, ProductViewSet

app_name = "api"
router = routers.SimpleRouter()
router.register("contacts", ContactViewSet, basename="contacts")
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
    path("auth/get_token/", GetAuthTokenView.as_view(), name="get_token"),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    # path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("", include(router.urls)),
]
