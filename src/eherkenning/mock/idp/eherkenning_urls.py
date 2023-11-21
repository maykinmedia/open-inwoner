from django.urls import path

from eherkenning.mock.idp.views.eherkenning import (
    eHerkenningMockIDPLoginView,
    eHerkenningMockIDPPasswordLoginView,
)

app_name = "eherkenning-mock"

urlpatterns = [
    path("inloggen/", eHerkenningMockIDPLoginView.as_view(), name="login"),
    path(
        "inloggen_ww/", eHerkenningMockIDPPasswordLoginView.as_view(), name="password"
    ),
]
