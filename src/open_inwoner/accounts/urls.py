from django.urls import path

from .views import InboxPrivateMediaView, InboxStartView, InboxView

app_name = "accounts"
urlpatterns = [
    path("inbox/", InboxView.as_view(), name="inbox"),
    path("inbox/conversation/<str:uuid>/", InboxView.as_view(), name="inbox"),
    path("inbox/start/", InboxStartView.as_view(), name="inbox_start"),
    path(
        "inbox/files/<str:uuid>/download/",
        InboxPrivateMediaView.as_view(),
        name="inbox_download",
    ),
]
