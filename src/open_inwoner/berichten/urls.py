from django.urls import path

from open_inwoner.berichten.views.bericht_detail import BerichtDownloadView

from .views import BerichtDetailView, BerichtListView, MarkBerichtUnreadView

app_name = "berichten"

urlpatterns = [
    path("<uuid:object_uuid>/", BerichtDetailView.as_view(), name="detail"),
    path(
        "<uuid:object_uuid>/mark-unread",
        MarkBerichtUnreadView.as_view(),
        name="mark-bericht-unread",
    ),
    path(
        "<uuid:object_uuid>/download",
        BerichtDownloadView.as_view(),
        name="download-bericht-attachment",
    ),
    path("", BerichtListView.as_view(), name="list"),
]
