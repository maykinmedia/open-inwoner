from django.urls import path

from open_inwoner.accounts.views.inbox import (
    InboxPrivateMediaView,
    InboxStartView,
    InboxView,
)

app_name = "inbox"

urlpatterns = [
    path("", InboxView.as_view(), name="index"),
    path("conversation/<str:uuid>/", InboxView.as_view(), name="index"),
    path("start/", InboxStartView.as_view(), name="start"),
    path(
        "files/<str:uuid>/download/",
        InboxPrivateMediaView.as_view(),
        name="download",
    ),
]
