from django.urls import path

from .views import (
    PlanCreateView,
    PlanDetailView,
    PlanFileUploadView,
    PlanGoalEditView,
    PlanListView,
)

app_name = "plans"
urlpatterns = [
    path("", PlanListView.as_view(), name="plan_list"),
    path("create/", PlanCreateView.as_view(), name="plan_create"),
    path("<uuid:uuid>/", PlanDetailView.as_view(), name="plan_detail"),
    path("<uuid:uuid>/edit/goal/", PlanGoalEditView.as_view(), name="plan_edit_goal"),
    path("<uuid:uuid>/add/file/", PlanFileUploadView.as_view(), name="plan_add_file"),
]
