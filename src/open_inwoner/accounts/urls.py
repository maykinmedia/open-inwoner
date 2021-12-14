from django.urls import path
from open_inwoner.pdc.views import HomeView
from .views.inbox import InboxView

app_name = "accounts"
urlpatterns = [
    path("inbox/", InboxView.as_view(), name="inbox"),
    path("setup/", HomeView.as_view(), name="setup_1"),
    path("", HomeView.as_view(), name="my_profile"),
]
