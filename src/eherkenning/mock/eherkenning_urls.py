from django.urls import path

from eherkenning.mock.views.eherkenning import (
    eHerkenningAssertionConsumerServiceMockView,
    eHerkenningLoginMockView,
)

"""
this is a mock replacement for the regular eherkenning_urls.py
"""

app_name = "eherkenning"

urlpatterns = (
    path("login/", eHerkenningLoginMockView.as_view(), name="login"),
    path("acs/", eHerkenningAssertionConsumerServiceMockView.as_view(), name="acs"),
)
