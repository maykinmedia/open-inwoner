from django.urls import path

from open_inwoner.ssd.views.benefits_views import BenefitsOverview

app_name = "ssd"

urlpatterns = [
    path("", BenefitsOverview.as_view(), name="benefits_index"),
]
