from django.urls import path

from .views import ProductDetailView, ProductListView

app_name = "mijn_producten"

urlpatterns = [
    path("", ProductListView.as_view(), name="mijn-product-list"),
    path(
        "<uuid:product_uuid>/", ProductDetailView.as_view(), name="mijn-product-detail"
    ),
]
