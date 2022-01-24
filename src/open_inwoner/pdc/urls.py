from unicodedata import category

from django.urls import include, path

from .views import CategoryDetailView, CategoryListView, ProductDetailView

PRODUCT_PATH_NAME = "products"

product_urls = [
    path(
        f"{PRODUCT_PATH_NAME}/<str:slug>/",
        ProductDetailView.as_view(),
        name="product_detail",
    )
]

category_url = [
    path("<str:slug>/", CategoryDetailView.as_view(), name="category_detail"),
    path("<str:slug>/", include(category_url, namespace="pdc")),
    path("<str:slug>/", include(product_urls, namespace="pdc")),
]

app_name = "pdc"
urlpatterns = [
    path("themas/", CategoryListView.as_view(), name="category_list"),
    path("themas/<str:slug>/", CategoryDetailView.as_view(), name="category_detail"),
    path(
        f"{PRODUCT_PATH_NAME}/<str:slug>/",
        ProductDetailView.as_view(),
        name="product_detail",
    ),
]
