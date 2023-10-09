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
    InnerCaseListView,
    OuterCaseDetailView,
    OuterCaseListView,
)

app_name = "cases"

urlpatterns = [
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
    path("open/", RedirectView.as_view(), name="redirect"),
    path("content/", InnerCaseListView.as_view(), name="cases_content"),
    path("", OuterCaseListView.as_view(), name="index"),
]
