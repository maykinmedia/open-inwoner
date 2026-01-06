from django.urls import path

from .views import AfvalView

app_name = "mijn_afval"


urlpatterns = [path("", AfvalView.as_view(), name="index")]
