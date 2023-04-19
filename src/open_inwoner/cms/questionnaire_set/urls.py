from django.urls import path

from open_inwoner.questionnaire.views import (
    QuestionnaireExportView,
    QuestionnaireResetView,
    QuestionnaireRootListView,
    QuestionnaireStepView,
)

app_name = "questionnaire_set"

urlpatterns = [
    path("reset", QuestionnaireResetView.as_view(), name="reset"),
    path("<str:slug>", QuestionnaireStepView.as_view(), name="root_step"),
    path(
        "<str:root_slug>/<str:slug>",
        QuestionnaireStepView.as_view(),
        name="descendent_step",
    ),
    path("export/", QuestionnaireExportView.as_view(), name="questionnaire_export"),
    path("", QuestionnaireRootListView.as_view(), name="questionnaire_list"),
]
