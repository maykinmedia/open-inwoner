from django.urls import include, path, re_path

from .views import CategoryDetailView, CategoryListView, ProductDetailView

PRODUCT_PATH_NAME = "products"

app_name = "pdc"
urlpatterns = [
    path("themas/", CategoryListView.as_view(), name="category_list"),
    re_path(
        r"^themas/(?P<slug>[\w\-\/]+)/products/<str:slug>/$",
        ProductDetailView.as_view(),
        name="category_product_detail",
    ),
    re_path(
        r"^themas/(?P<slug>[\w\-\/]+)/$",
        CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path(
        f"{PRODUCT_PATH_NAME}/<str:slug>/",
        ProductDetailView.as_view(),
        name="product_detail",
    ),
]
