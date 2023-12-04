from django.urls import path

from eherkenning.mock.views.eherkenning import (
    eHerkenningAssertionConsumerServiceMockView,
    eHerkenningLoginMockView,
    eHerkenningLogoutMockView,
)

"""
this is a mock replacement for the regular eherkenning_urls.py
"""

app_name = "eherkenning"

urlpatterns = (
    path("login/", eHerkenningLoginMockView.as_view(), name="login"),
    path("acs/", eHerkenningAssertionConsumerServiceMockView.as_view(), name="acs"),
    path("logout/", eHerkenningLogoutMockView.as_view(), name="logout"),
)
