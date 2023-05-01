from django.urls import include, path, re_path
from django.views.generic import RedirectView

from open_inwoner.pdc.views import (
    CategoryDetailView,
    CategoryListView,
    ProductDetailView,
    ProductFinderView,
    ProductFormView,
    ProductLocationDetailView,
)

app_name = "products"

urlpatterns = [
    path("ontdekken/", ProductFinderView.as_view(), name="product_finder"),
    path(
        "locaties/<str:uuid>",
        ProductLocationDetailView.as_view(),
        name="location_detail",
    ),
    path(
        f"producten/<str:slug>/formulier/",
        ProductFormView.as_view(),
        name="product_form",
    ),
    path(
        # Required to handle dynamic URL-paths appended by Open Forms.
        f"producten/<str:slug>/formulier/<path:rest>",
        ProductFormView.as_view(),
        name="product_form",
    ),
    path(
        f"producten/<str:slug>/",
        ProductDetailView.as_view(),
        name="product_detail",
    ),
    path(
        f"producten/",
        RedirectView.as_view(pattern_name="products:category_list"),
        name="product_detail",
    ),
    re_path(
        r"^(?P<category_slug>[\w\-\/]+)/producten/(?P<slug>[\w\-]+)/$",
        ProductDetailView.as_view(),
        name="category_product_detail",
    ),
    re_path(
        r"^(?P<slug>[\w\-\/]+)/$",
        CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path("", CategoryListView.as_view(), name="category_list"),
]
