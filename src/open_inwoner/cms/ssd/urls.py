from django.urls import path

from open_inwoner.ssd.views.benefits_views import (
    BenefitsOverview,
    DownloadMonthlyBenefitsView,
    DownloadYearlyBenefitsView,
)

app_name = "ssd"


urlpatterns = [
    path("", BenefitsOverview.as_view(), name="benefits_index"),
    path(
        "jaaropgaven/<str:file_name>/download",
        DownloadYearlyBenefitsView.as_view(),
        name="download_yearly_benefits",
    ),
    path(
        "maandspecificaties/<str:file_name>/download",
        DownloadMonthlyBenefitsView.as_view(),
        name="download_monthly_benefits",
    ),
]
