from django.urls import path

from .views import BerichtDetailView, BerichtListView, MarkBerichtUnreadView

app_name = "berichten"

urlpatterns = [
    path("<uuid:object_uuid>/", BerichtDetailView.as_view(), name="detail"),
    path(
        "<uuid:object_uuid>/mark-unread",
        MarkBerichtUnreadView.as_view(),
        name="mark-bericht-unread",
    ),
    path("", BerichtListView.as_view(), name="list"),
]
