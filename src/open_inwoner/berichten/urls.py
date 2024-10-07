from django.urls import path

from open_inwoner.berichten.views.bericht_detail import BerichtDetailView

from .views import BerichtListView

app_name = "berichten"

urlpatterns = [
    path("<uuid:object_uuid>/", BerichtDetailView.as_view(), name="detail"),
    path("", BerichtListView.as_view(), name="list"),
]
