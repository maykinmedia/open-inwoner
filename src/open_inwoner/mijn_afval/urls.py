from django.urls import path

from .views import MijnAfvalListView

app_name = "mijn_afval"


urlpatterns = [path("", MijnAfvalListView.as_view(), name="list")]
