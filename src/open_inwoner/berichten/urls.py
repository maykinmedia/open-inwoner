from django.urls import path

from .views import BerichtDetailView, BerichtListView, mark_bericht_as_unread

app_name = "berichten"

urlpatterns = [
    path("<uuid:object_uuid>/", BerichtDetailView.as_view(), name="detail"),
    path(
        "<uuid:object_uuid>/mark-unread",
        mark_bericht_as_unread,
        name="mark-bericht-unread",
    ),
    path("", BerichtListView.as_view(), name="list"),
]
