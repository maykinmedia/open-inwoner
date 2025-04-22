from django.urls import path

from open_inwoner.plans.views import (
    PlanActionCreateView,
    PlanActionDeleteView,
    PlanActionEditStatusTagView,
    PlanActionEditView,
    PlanActionHistoryView,
    PlanCreateFromTemplateView,
    PlanCreateView,
    PlanDetailView,
    PlanEditView,
    PlanExportView,
    PlanFileUploadView,
    PlanGoalEditView,
    PlanListView,
    PlanTemplateChoiceView,
)

app_name = "collaborate"

urlpatterns = [
    path("", PlanListView.as_view(), name="plan_list"),
    path(
        "choose-template/",
        PlanTemplateChoiceView.as_view(),
        name="plan_choose_template",
    ),
    path("create/", PlanCreateView.as_view(), name="plan_create"),
    path(
        "create-from-template/<int:template_id>/",
        PlanCreateFromTemplateView.as_view(),
        name="plan_create_from_template",
    ),
    path("<uuid:uuid>/", PlanDetailView.as_view(), name="plan_detail"),
    path("<uuid:uuid>/edit/", PlanEditView.as_view(), name="plan_edit"),
    path("<uuid:uuid>/edit/goal/", PlanGoalEditView.as_view(), name="plan_edit_goal"),
    path("<uuid:uuid>/add/file/", PlanFileUploadView.as_view(), name="plan_add_file"),
    path(
        "<uuid:uuid>/actions/add/",
        PlanActionCreateView.as_view(),
        name="plan_action_create",
    ),
    path(
        "<uuid:plan_uuid>/actions/<uuid:uuid>/edit/",
        PlanActionEditView.as_view(),
        name="plan_action_edit",
    ),
    path(
        "<uuid:plan_uuid>/actions/<uuid:uuid>/edit/status/",
        PlanActionEditStatusTagView.as_view(),
        name="plan_action_edit_status",
    ),
    path(
        "<uuid:plan_uuid>/actions/<uuid:uuid>/delete/",
        PlanActionDeleteView.as_view(),
        name="plan_action_delete",
    ),
    path(
        "<uuid:plan_uuid>/actions/<str:uuid>/history/",
        PlanActionHistoryView.as_view(),
        name="plan_action_history",
    ),
    path("<uuid:uuid>/export/", PlanExportView.as_view(), name="plan_export"),
]
