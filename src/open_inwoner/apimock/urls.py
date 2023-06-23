from django.urls import path

from open_inwoner.apimock.views import APIMockView

app_name = "apimock"

urlpatterns = [
    path(
        "<slug:set_name>/<slug:api_name>/<path:endpoint>",
        APIMockView.as_view(),
        name="mock",
    ),
]
