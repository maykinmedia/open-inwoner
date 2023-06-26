from django.urls import include, path

from open_inwoner.accounts.views import (
    ActionCreateView,
    ActionExportView,
    ActionHistoryView,
    ActionListExportView,
    ActionListView,
    ActionPrivateMediaView,
    ActionUpdateStatusTagView,
    ActionUpdateView,
    ContactApprovalView,
    ContactCreateView,
    ContactDeleteView,
    ContactListView,
    DocumentDeleteView,
    DocumentPrivateMediaView,
    EditProfileView,
    InviteAcceptView,
    MyCategoriesView,
    MyDataView,
    MyNotificationsView,
    MyProfileExportView,
    MyProfileView,
    NecessaryFieldsUserView,
)
from open_inwoner.accounts.views.actions import ActionDeleteView
from open_inwoner.ssd.views.benefits_views import BenefitsOverview

app_name = "profile"

action_patterns = [
    path("create/", ActionCreateView.as_view(), name="action_create"),
    path("export/", ActionListExportView.as_view(), name="action_list_export"),
    path("<str:uuid>/edit/", ActionUpdateView.as_view(), name="action_edit"),
    path(
        "<str:uuid>/edit/status/",
        ActionUpdateStatusTagView.as_view(),
        name="action_edit_status",
    ),
    path(
        "<str:uuid>/delete/",
        ActionDeleteView.as_view(),
        name="action_delete",
    ),
    path(
        "<str:uuid>/export/",
        ActionExportView.as_view(),
        name="action_export",
    ),
    path(
        "<str:uuid>/download/",
        ActionPrivateMediaView.as_view(),
        name="action_download",
    ),
    path(
        "<str:uuid>/history/",
        ActionHistoryView.as_view(),
        name="action_history",
    ),
    path("", ActionListView.as_view(), name="action_list"),
]

benefits_patterns = [
    path("", BenefitsOverview.as_view(), name="benefits_index"),
]

contact_patterns = [
    path("create/", ContactCreateView.as_view(), name="contact_create"),
    path(
        "<str:uuid>/delete/",
        ContactDeleteView.as_view(),
        name="contact_delete",
    ),
    path(
        "<str:uuid>/approval/",
        ContactApprovalView.as_view(),
        name="contact_approval",
    ),
    path("", ContactListView.as_view(), name="contact_list"),
]

documents_patterns = [
    path(
        "<str:uuid>/delete/",
        DocumentDeleteView.as_view(),
        name="documents_delete",
    ),
    path(
        "<str:uuid>/download/",
        DocumentPrivateMediaView.as_view(),
        name="documents_download",
    ),
]

urlpatterns = [
    path("actions/", include(action_patterns)),
    path("contacts/", include(contact_patterns)),
    path("uitkeringen/", include(benefits_patterns)),
    path("documenten/", include(documents_patterns)),
    path("onderwerpen/", MyCategoriesView.as_view(), name="categories"),
    path("notificaties/", MyNotificationsView.as_view(), name="notifications"),
    path("mydata/", MyDataView.as_view(), name="data"),
    path("edit/", EditProfileView.as_view(), name="edit"),
    path("invite/<str:key>/accept/", InviteAcceptView.as_view(), name="invite_accept"),
    path("export/", MyProfileExportView.as_view(), name="export"),
    path(
        "register/necessary/",
        NecessaryFieldsUserView.as_view(),
        name="registration_necessary",
    ),
    path("", MyProfileView.as_view(), name="detail"),
]
