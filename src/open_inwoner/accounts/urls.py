from django.urls import path

from open_inwoner.pdc.views import HomeView

from .views import (
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
    DocumentCreateView,
    DocumentDeleteView,
    DocumentPrivateMediaView,
    EditProfileView,
    InboxPrivateMediaView,
    InboxStartView,
    InboxView,
    InviteAcceptView,
    MyCategoriesView,
    MyDataView,
    MyProfileExportView,
    MyProfileView,
    NecessaryFieldsUserView,
)
from .views.actions import ActionDeleteView

app_name = "accounts"
urlpatterns = [
    path("inbox/", InboxView.as_view(), name="inbox"),
    path("inbox/conversation/<str:uuid>/", InboxView.as_view(), name="inbox"),
    path("inbox/start/", InboxStartView.as_view(), name="inbox_start"),
    path(
        "inbox/files/<str:uuid>/download/",
        InboxPrivateMediaView.as_view(),
        name="inbox_download",
    ),
    path("setup/", HomeView.as_view(), name="setup_1"),
    path("documents/create/", DocumentCreateView.as_view(), name="documents_create"),
    path(
        "documents/<str:uuid>/delete/",
        DocumentDeleteView.as_view(),
        name="documents_delete",
    ),
    path(
        "documents/<str:uuid>/download/",
        DocumentPrivateMediaView.as_view(),
        name="documents_download",
    ),
    path("actions/create/", ActionCreateView.as_view(), name="action_create"),
    path("actions/export/", ActionListExportView.as_view(), name="action_list_export"),
    path("actions/<str:uuid>/edit/", ActionUpdateView.as_view(), name="action_edit"),
    path(
        "actions/<str:uuid>/edit/status/",
        ActionUpdateStatusTagView.as_view(),
        name="action_edit_status",
    ),
    path(
        "actions/<str:uuid>/delete/",
        ActionDeleteView.as_view(),
        name="action_delete",
    ),
    path(
        "actions/<str:uuid>/export/",
        ActionExportView.as_view(),
        name="action_export",
    ),
    path(
        "actions/<str:uuid>/download/",
        ActionPrivateMediaView.as_view(),
        name="action_download",
    ),
    path(
        "actions/<str:uuid>/history/",
        ActionHistoryView.as_view(),
        name="action_history",
    ),
    path("actions/", ActionListView.as_view(), name="action_list"),
    path("contacts/create/", ContactCreateView.as_view(), name="contact_create"),
    path(
        "contacts/<str:uuid>/delete/",
        ContactDeleteView.as_view(),
        name="contact_delete",
    ),
    path(
        "contacts/<str:uuid>/approval/",
        ContactApprovalView.as_view(),
        name="contact_approval",
    ),
    path("contacts/", ContactListView.as_view(), name="contact_list"),
    path("onderwerpen/", MyCategoriesView.as_view(), name="my_categories"),
    path("mydata/", MyDataView.as_view(), name="my_data"),
    path("edit/", EditProfileView.as_view(), name="edit_profile"),
    path("invite/<str:key>/accept/", InviteAcceptView.as_view(), name="invite_accept"),
    path("export/", MyProfileExportView.as_view(), name="profile_export"),
    path(
        "register/necessary/",
        NecessaryFieldsUserView.as_view(),
        name="registration_necessary",
    ),
    path("", MyProfileView.as_view(), name="my_profile"),
]
