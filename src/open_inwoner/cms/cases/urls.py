from django.urls import path
from django.views.generic import RedirectView

from open_inwoner.accounts.views.contactmoments import (
    KlantContactMomentDetailView,
    KlantContactMomentListView,
)

from .views import (
    CaseContactFormView,
    CaseDocumentDownloadView,
    CaseDocumentUploadFormView,
    InnerCaseDetailView,
    InnerClosedCaseListView,
    InnerOpenCaseListView,
    InnerOpenSubmissionListView,
    OuterCaseDetailView,
    OuterClosedCaseListView,
    OuterOpenCaseListView,
    OuterOpenSubmissionListView,
)

app_name = "cases"

urlpatterns = [
    path(
        "closed/content/",
        InnerClosedCaseListView.as_view(),
        name="closed_cases_content",
    ),
    path("closed/", OuterClosedCaseListView.as_view(), name="closed_cases"),
    path("forms/", OuterOpenSubmissionListView.as_view(), name="open_submissions"),
    path(
        "forms/content/",
        InnerOpenSubmissionListView.as_view(),
        name="open_submissions_content",
    ),
    path(
        "contactmomenten/",
        KlantContactMomentListView.as_view(),
        name="contactmoment_list",
    ),
    path(
        "contactmomenten/<str:kcm_uuid>/",
        KlantContactMomentDetailView.as_view(),
        name="contactmoment_detail",
    ),
    path(
        "<str:object_id>/document/<str:info_id>/",
        CaseDocumentDownloadView.as_view(),
        name="document_download",
    ),
    path(
        "<str:object_id>/status/content/",
        InnerCaseDetailView.as_view(),
        name="case_detail_content",
    ),
    path(
        "<str:object_id>/status/",
        OuterCaseDetailView.as_view(),
        name="case_detail",
    ),
    path(
        "<str:object_id>/status/contact-form/",
        CaseContactFormView.as_view(),
        name="case_detail_contact_form",
    ),
    path(
        "<str:object_id>/status/document-form/",
        CaseDocumentUploadFormView.as_view(),
        name="case_detail_document_form",
    ),
    path("open/", RedirectView.as_view(pattern_name="cases:open_cases"), name="index"),
    path("content/", InnerOpenCaseListView.as_view(), name="open_cases_content"),
    path("", OuterOpenCaseListView.as_view(), name="open_cases"),
]
