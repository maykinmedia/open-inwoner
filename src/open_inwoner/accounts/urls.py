from django.urls import path

from open_inwoner.pdc.views import HomeView

from .views import (
    ActionCreateView,
    ActionExportView,
    ActionListExportView,
    ActionListView,
    ActionUpdateView,
    CasesListView,
    CasesStatusView,
    ContactCreateView,
    ContactDeleteView,
    ContactListView,
    ContactUpdateView,
    DocumentCreateView,
    DocumentDeleteView,
    EditProfileView,
    InboxStartView,
    InboxView,
    InviteAcceptView,
    MyCategoriesView,
    MyProfileExportView,
    MyProfileView,
)

app_name = "accounts"
urlpatterns = [
    path("inbox/", InboxView.as_view(), name="inbox"),
    path("inbox/start/", InboxStartView.as_view(), name="inbox_start"),
    path("setup/", HomeView.as_view(), name="setup_1"),
    path("documents/create/", DocumentCreateView.as_view(), name="documents_create"),
    path(
        "documents/<str:uuid>/delete/",
        DocumentDeleteView.as_view(),
        name="documents_delete",
    ),
    path("actions/create/", ActionCreateView.as_view(), name="action_create"),
    path("actions/export/", ActionListExportView.as_view(), name="action_list_export"),
    path("actions/<str:uuid>/edit/", ActionUpdateView.as_view(), name="action_edit"),
    path(
        "actions/<str:uuid>/delete/",
        ActionUpdateView.as_view(),
        name="action_delete",
    ),
    path(
        "actions/<str:uuid>/export/",
        ActionExportView.as_view(),
        name="action_export",
    ),
    path("actions/", ActionListView.as_view(), name="action_list"),
    path("contacts/create/", ContactCreateView.as_view(), name="contact_create"),
    path("contacts/<str:uuid>/edit/", ContactUpdateView.as_view(), name="contact_edit"),
    path(
        "contacts/<str:uuid>/delete/",
        ContactDeleteView.as_view(),
        name="contact_delete",
    ),
    path("contacts/", ContactListView.as_view(), name="contact_list"),
    path("themes/", MyCategoriesView.as_view(), name="my_themes"),
    path("cases/", CasesListView.as_view(), name="my_cases"),
    path(
        "cases/<str:object_id>/status/",
        CasesStatusView.as_view(),
        name="case_status",
    ),
    path("edit/", EditProfileView.as_view(), name="edit_profile"),
    path("invite/<str:key>/accept/", InviteAcceptView.as_view(), name="invite_accept"),
    path("export/", MyProfileExportView.as_view(), name="profile_export"),
    path("", MyProfileView.as_view(), name="my_profile"),
]
