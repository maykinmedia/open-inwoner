from django.urls import path

from open_inwoner.pdc.views import HomeView

from .views import (
    ActionCreateView,
    ActionListView,
    ActionUpdateView,
    ContactCreateView,
    ContactListView,
    ContactUpdateView,
    DocumentCreateView,
    DocumentDeleteView,
    EditProfileView,
    MyCategoriesView,
    MyProfileView,
)
from .views.inbox import InboxView

app_name = "accounts"
urlpatterns = [
    path("inbox/", InboxView.as_view(), name="inbox"),
    path("setup/", HomeView.as_view(), name="setup_1"),
    path("documents/create/", DocumentCreateView.as_view(), name="documents_create"),
    path(
        "documents/<str:uuid>/delete/",
        DocumentDeleteView.as_view(),
        name="documents_delete",
    ),
    path("actions/create/", ActionCreateView.as_view(), name="action_create"),
    path("actions/<str:uuid>/edit/", ActionUpdateView.as_view(), name="action_edit"),
    path(
        "actions/<str:uuid>/delete/",
        ActionUpdateView.as_view(),
        name="action_delete",
    ),
    path("actions/", ActionListView.as_view(), name="action_list"),
    path("contacts/create/", ContactCreateView.as_view(), name="contact_create"),
    path("contacts/<str:uuid>/edit/", ContactUpdateView.as_view(), name="contact_edit"),
    path(
        "contacts/<str:uuid>/delete/",
        ContactUpdateView.as_view(),
        name="contact_delete",
    ),
    path("contacts/", ContactListView.as_view(), name="contact_list"),
    path("themes/", MyCategoriesView.as_view(), name="my_themes"),
    path("edit/", EditProfileView.as_view(), name="edit_profile"),
    path("", MyProfileView.as_view(), name="my_profile"),
]
