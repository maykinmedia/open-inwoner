from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from webtest import Upload
from freezegun import freeze_time
from privates.test import temp_private_root
from timeline_logger.models import TimelineLog

from open_inwoner.pdc.tests.factories import CategoryFactory
from open_inwoner.utils.logentry import LOG_ACTIONS

from ..models import User, Contact, Document
from .factories import ContactFactory, DocumentFactory, UserFactory


class TestProfile(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()

    @freeze_time("2021-10-18 13:00:00")
    def test_registration_is_logged(self):
        user = UserFactory.build()
        form = self.app.get(reverse("django_registration_register")).forms[
            "registration-form"
        ]
        form["email"] = user.email
        form["first_name"] = user.first_name
        form["last_name"] = user.last_name
        form["password1"] = user.password
        form["password2"] = user.password
        form.submit()
        log_entry = TimelineLog.objects.first()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, User.objects.all()[1].id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("user was created"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": user.email,
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_users_modification_is_logged(self):
        form = self.app.get(reverse("accounts:edit_profile"), user=self.user).forms[
            "profile-edit"
        ]
        form["first_name"] = "Updated name"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, User.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("user profile was modified"),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": self.user.email,
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_categories_modification_is_logged(self):
        CategoryFactory()
        CategoryFactory()
        form = self.app.get(reverse("accounts:my_themes"), user=self.user).forms[
            "change-themes"
        ]

        form.get("selected_themes", index=1).checked = True
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, User.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("user's categories were modified"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_login_via_admin_is_logged(self):
        self.app.post(reverse("admin:login"), user=self.user)
        log_entry = TimelineLog.objects.first()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, User.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("user was logged in via admin page"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_login_via_frontend_is_logged(self):
        self.app.post(reverse("login"), user=self.user)
        log_entry = TimelineLog.objects.first()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, User.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("user was logged in via frontend"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_logout_is_logged(self):
        self.app.get(reverse("logout"), user=self.user)
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, User.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("user was logged out"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )


class TestContacts(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()
        self.contact = ContactFactory(created_by=self.user)

    @freeze_time("2021-10-18 13:00:00")
    def test_contact_addition_is_logged(self):
        contact = ContactFactory.build(created_by=self.user)
        form = self.app.get(reverse("accounts:contact_create"), user=self.user).forms[
            "contact-form"
        ]
        form["email"] = contact.email
        form["first_name"] = contact.first_name
        form["last_name"] = contact.last_name
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(
            log_entry.content_object.id, Contact.objects.get(email=contact.email).id
        )
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("contact was created"),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": f"{contact.first_name} {contact.last_name}",
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_contact_update_is_logged(self):
        form = self.app.get(
            reverse("accounts:contact_edit", kwargs={"uuid": self.contact.uuid}),
            user=self.user,
        ).forms["contact-form"]
        form["email"] = "updated@email.com"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Contact.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("contact was modified"),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": f"{self.contact.first_name} {self.contact.last_name}",
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_contact_deletion_is_logged(self):
        contact_id = self.contact.id
        self.app.post(
            reverse("accounts:contact_delete", kwargs={"uuid": self.contact.uuid}),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.object_id, str(contact_id))
        self.assertEquals(
            log_entry.extra_data,
            {
                "action_flag": list(LOG_ACTIONS[DELETION]),
                "content_object_repr": f"{self.contact.first_name} {self.contact.last_name}",
                "message": _("contact was deleted"),
            },
        )


class TestDocuments(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()
        self.document = DocumentFactory(owner=self.user)

    @freeze_time("2021-10-18 13:00:00")
    def test_document_download_is_logged(self):
        self.app.get(
            reverse("accounts:documents_download", kwargs={"uuid": self.document.uuid}),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Document.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("file was downloaded"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.document.name,
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    @temp_private_root()
    def test_document_upload_is_logged(self):
        form = self.app.get(
            reverse("accounts:documents_create"),
            user=self.user,
        ).forms["document-create"]
        form["name"] = "readme"
        form["file"] = Upload("readme.png", b"data", "image/png")
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Document.objects.all()[1].id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("file was uploaded"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": "readme",
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    @temp_private_root()
    def test_document_deletion_is_logged(self):
        self.app.get(
            reverse("accounts:documents_delete", kwargs={"uuid": self.document.uuid}),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, self.document.id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("file was deleted"),
                "action_flag": list(LOG_ACTIONS[3]),
                "content_object_repr": "readme",
            },
        )
