from django.urls import path

from .views import afval_view

app_name = "mijn_afval"


urlpatterns = [path("", afval_view, name="index")]
