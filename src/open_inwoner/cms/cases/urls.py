from django.urls import path

from open_inwoner.accounts.views.contactmoments import (
    KlantContactMomentDetailView,
    KlantContactMomentListView,
    KlantContactMomentRedirectView,
)

from .views import (
    CaseContactFormView,
    CaseDocumentDownloadView,
    CaseDocumentUploadFormView,
    InnerCaseDetailView,
    InnerCaseListView,
    LegacyCaseDetailHandler,
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
        "contactmomenten/<str:api_service>/<str:kcm_uuid>/",
        KlantContactMomentDetailView.as_view(),
        name="contactmoment_detail",
    ),
    path(
        "contactmoment/<str:uuid>/",
        KlantContactMomentRedirectView.as_view(),
        name="kcm_redirect",
    ),
    path(
        "<str:api_group_id>/<str:object_id>/document/<str:info_id>/",
        CaseDocumentDownloadView.as_view(),
        name="document_download",
    ),
    path(
        "<str:api_group_id>/<str:object_id>/status/content/",
        InnerCaseDetailView.as_view(),
        name="case_detail_content",
    ),
    path(
        "<str:api_group_id>/<str:object_id>/status/",
        OuterCaseDetailView.as_view(),
        name="case_detail",
    ),
    path(
        "<str:api_group_id>/<str:object_id>/status/contact-form/",
        CaseContactFormView.as_view(),
        name="case_detail_contact_form",
    ),
    path(
        "<str:api_group_id>/<str:object_id>/status/document-form/",
        CaseDocumentUploadFormView.as_view(),
        name="case_detail_document_form",
    ),
    path("content/", InnerCaseListView.as_view(), name="cases_content"),
    path("", OuterCaseListView.as_view(), name="index"),
    # Legacy redirects for hard-coded case detail urls lacking a ZGW api group reference
    # in the url (e.g. from old notification mails). This redirects those URLs
    # to the new case detail URL with a reference to the only ZGW api group (if 1),
    # or the case list page with an expiration notice (because we can't be sure which
    # api group to use).
    path(
        "<str:object_id>/status/",
        LegacyCaseDetailHandler.as_view(),
        name="legacy_case_detail",
    ),
]
