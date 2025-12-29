from .zaken_detail import (
    CaseContactFormView,
    CaseDocumentDownloadView,
    CaseDocumentUploadFormView,
    InnerCaseDetailView,
    LegacyCaseDetailHandler,
    OuterCaseDetailView,
)
from .zaken_list import InnerCaseListView, OuterCaseListView

__all__ = [
    "InnerCaseListView",
    "OuterCaseListView",
    "CaseContactFormView",
    "CaseDocumentDownloadView",
    "CaseDocumentUploadFormView",
    "InnerCaseDetailView",
    "LegacyCaseDetailHandler",
    "OuterCaseDetailView",
]
