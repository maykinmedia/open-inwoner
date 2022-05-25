from django.urls import path

from .views import RestartSessionView

app_name = "sessions"
urlpatterns = [
    path("restart/", RestartSessionView.as_view(), name="restart-session"),
]
