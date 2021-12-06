from django.urls import path

from open_inwoner.pdc.views import HomeView

app_name = "accounts"
urlpatterns = [
    path("setup/", HomeView.as_view(), name="setup_1"),
    path("", HomeView.as_view(), name="my_profile"),
]
