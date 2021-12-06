from django.urls import path

from .views import CategoryDetailView, CategoryListView, ProductDetailView

product_urls = [
    path("products/<str:slug>/", ProductDetailView.as_view(), name="product_detail")
]

app_name = "pdc"
urlpatterns = [
    path("themas/", CategoryListView.as_view(), name="category_list"),
    path("themas/<str:slug>/", CategoryDetailView.as_view(), name="category_detail"),
    path("products/<str:slug>/", ProductDetailView.as_view(), name="product_detail"),
]
