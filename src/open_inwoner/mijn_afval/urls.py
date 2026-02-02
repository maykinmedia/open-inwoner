from django.urls import path

from .views import AfvalProfielView

app_name = "mijn_afval"


urlpatterns = [
    path("", AfvalProfielView.as_view(), name="afval-profiel"),
]
