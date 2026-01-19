from django.urls import path

from .views import (
    LocatieDetailView,
    ProductTypeDetailView,
    ThemaDetailView,
    ThemaListView,
)

app_name = "producten_catalogus"

urlpatterns = [
    # Thema list view
    path(
        "themas/",
        ThemaListView.as_view(),
        name="thema-list",
    ),
    # Thema detail view - uses slug
    path(
        "themas/<slug:slug>/",
        ThemaDetailView.as_view(),
        name="thema-detail",
    ),
    # Locatie detail view - uses ID
    path(
        "locaties/<int:locatie_id>/",
        LocatieDetailView.as_view(),
        name="locatie-detail",
    ),
    # ProductType detail view - uses ID
    path(
        "product-typen/<int:product_type_id>/",
        ProductTypeDetailView.as_view(),
        name="product-type-detail",
    ),
]
