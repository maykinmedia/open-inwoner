from django.urls import path

from open_inwoner.ssd.views import MonthlyBenefitsFormView, YearlyBenefitsFormView

app_name = "ssd"


urlpatterns = [
    path(
        "",
        MonthlyBenefitsFormView.as_view(),
        name="uitkeringen",
    ),
    path(
        "maandspecificaties/",
        MonthlyBenefitsFormView.as_view(),
        name="monthly_benefits_index",
    ),
    path(
        "jaaropgaven/", YearlyBenefitsFormView.as_view(), name="yearly_benefits_index"
    ),
]
