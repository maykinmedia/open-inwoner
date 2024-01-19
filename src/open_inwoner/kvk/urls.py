from django.urls import path

from .views import CompanyBranchChoiceView

app_name = "kvk"

urlpatterns = [
    path("branches/", CompanyBranchChoiceView.as_view(), name="branches"),
]
