from django.urls import path, re_path
from django.views.generic import RedirectView

from open_inwoner.pdc.views import (
    CategoryDetailView,
    CategoryListView,
    ProductDetailView,
    ProductFinderView,
    ProductFormView,
    ProductLocationDetailView,
)
from open_inwoner.questionnaire.views import (
    QuestionnaireExportView,
    QuestionnaireResetView,
    QuestionnaireRootListView,
    QuestionnaireStepView,
)

app_name = "products"

urlpatterns = [
    path("ontdekken/", ProductFinderView.as_view(), name="product_finder"),
    path("questionnaire/reset", QuestionnaireResetView.as_view(), name="reset"),
    path("questionnaire/<str:slug>", QuestionnaireStepView.as_view(), name="root_step"),
    path(
        "questionnaire/<str:root_slug>/<str:slug>",
        QuestionnaireStepView.as_view(),
        name="descendent_step",
    ),
    path(
        "questionnaire/export/",
        QuestionnaireExportView.as_view(),
        name="questionnaire_export",
    ),
    path(
        "questionnaire/", QuestionnaireRootListView.as_view(), name="questionnaire_list"
    ),
    path(
        "locaties/<str:uuid>",
        ProductLocationDetailView.as_view(),
        name="location_detail",
    ),
    path(
        "producten/<str:slug>/formulier/",
        ProductFormView.as_view(),
        name="product_form",
    ),
    path(
        # Required to handle dynamic URL-paths appended by Open Forms.
        "producten/<str:slug>/formulier/<path:rest>",
        ProductFormView.as_view(),
        name="product_form",
    ),
    path(
        "producten/<str:slug>/",
        ProductDetailView.as_view(),
        name="product_detail",
    ),
    path(
        "producten/",
        RedirectView.as_view(pattern_name="products:category_list"),
        name="product_detail",
    ),
    re_path(
        r"^(?P<category_slug>[\w\-\/]+)/producten/(?P<slug>[\w\-]+)/$",
        ProductDetailView.as_view(),
        name="category_product_detail",
    ),
    re_path(
        r"^(?P<slug>[\w\-\/]+)/$",
        CategoryDetailView.as_view(),
        name="category_detail",
    ),
    path("", CategoryListView.as_view(), name="category_list"),
]
