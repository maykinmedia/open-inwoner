from django.urls import path

from .views import RestartSessionView

urlpatterns = [
    path("restart/", RestartSessionView.as_view(), name="restart-session"),
]
