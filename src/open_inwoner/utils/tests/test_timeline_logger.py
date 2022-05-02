from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from freezegun import freeze_time
from timeline_logger.models import TimelineLog

from open_inwoner.accounts.models import Contact
from open_inwoner.accounts.tests.factories import ContactFactory, UserFactory

from ..admin import CustomTimelineLogAdmin
from ..logentry import LOG_ACTIONS


class TestAdminTimelineLogging(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.contact = ContactFactory.build()

    def add_instance(self):
        url = reverse("admin:accounts_contact_add")
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        form["email"] = self.contact.email
        form["created_by"] = self.user.id
        form.submit()

    @freeze_time("2021-10-18 13:00:00")
    def test_added_object_is_logged(self):
        self.add_instance()
        log_entry = TimelineLog.objects.last()
        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Contact.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("Toegevoegd."),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": self.contact.get_name(),
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_changed_object_is_logged(self):
        contact = ContactFactory()
        url = reverse("admin:accounts_contact_change", kwargs={"object_id": contact.id})
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = "Vasileios"
        form["last_name"] = contact.last_name
        form["email"] = contact.email
        form["created_by"] = self.user.id
        form.submit()

        log_entry = TimelineLog.objects.last()
        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Contact.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("Voornaam en Aangemaakt door gewijzigd."),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": f"Vasileios {contact.last_name}",
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_deleted_object_is_logged(self):
        contact = ContactFactory()
        url = reverse("admin:accounts_contact_delete", kwargs={"object_id": contact.id})
        delete_form = self.app.get(url, user=self.user).forms[0]
        delete_form.submit()

        log_entry = TimelineLog.objects.last()
        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": "",
                "action_flag": list(LOG_ACTIONS[DELETION]),
                "content_object_repr": contact.get_name(),
            },
        )

    def test_user_does_not_have_add_permission(self):
        url = reverse("admin:timeline_logger_timelinelog_add")
        response = self.app.get(url, user=self.user, expect_errors=True)
        self.assertEquals(response.status_code, 403)

    def test_user_does_not_have_change_permission(self):
        add_url = reverse("admin:accounts_contact_add")
        add_form = self.app.get(add_url, user=self.user).forms.get("contact_form")
        add_form["first_name"] = self.contact.first_name
        add_form["last_name"] = self.contact.last_name
        add_form["email"] = self.contact.email
        add_form["created_by"] = self.user.id
        add_form.submit()
        log_entry = TimelineLog.objects.first()
        log_url = reverse(
            "admin:timeline_logger_timelinelog_change",
            kwargs={"object_id": log_entry.id},
        )
        log_form = self.app.get(log_url, user=self.user).forms["timelinelog_form"]
        log_form["object_id"] = 29
        response = log_form.submit(expect_errors=True)
        self.assertEquals(response.status_code, 403)

    def test_user_does_not_have_delete_permission(self):
        add_url = reverse("admin:accounts_contact_add")
        add_form = self.app.get(add_url, user=self.user).forms.get("contact_form")
        add_form["first_name"] = self.contact.first_name
        add_form["last_name"] = self.contact.last_name
        add_form["email"] = self.contact.email
        add_form["created_by"] = self.user.id
        add_form.submit()
        log_entry = TimelineLog.objects.first()
        log_url = reverse(
            "admin:timeline_logger_timelinelog_delete",
            kwargs={"object_id": log_entry.id},
        )
        response = self.app.post(log_url, user=self.user, expect_errors=True)
        self.assertEquals(response.status_code, 403)

    def test_get_action_returns_addition_when_object_is_added(self):
        url = reverse("admin:accounts_contact_add")
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        form["email"] = self.contact.email
        form["created_by"] = self.user.id
        form.submit()

        log_entry = TimelineLog.objects.last()
        action = CustomTimelineLogAdmin.get_action_flag(
            CustomTimelineLogAdmin, log_entry
        )
        self.assertEquals(action, _("Aangemaakt"))

    def test_get_action_returns_change_when_object_is_modified(self):
        contact = ContactFactory()
        url = reverse("admin:accounts_contact_change", kwargs={"object_id": contact.id})
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = "Another name"
        form.submit()

        log_entry = TimelineLog.objects.last()
        action = CustomTimelineLogAdmin.get_action_flag(
            CustomTimelineLogAdmin, log_entry
        )
        self.assertEquals(action, _("Gewijzigd"))

    def test_get_action_returns_delete_when_object_is_deleted(self):
        contact = ContactFactory()
        url = reverse("admin:accounts_contact_delete", kwargs={"object_id": contact.id})
        form = self.app.get(url, user=self.user).forms[0]
        form.submit()

        log_entry = TimelineLog.objects.last()
        action = CustomTimelineLogAdmin.get_action_flag(
            CustomTimelineLogAdmin, log_entry
        )
        self.assertEquals(action, _("Verwijderd"))

    def test_get_action_returns_empty_string_when_no_extra_data_exists(self):
        contact = ContactFactory()
        TimelineLog.objects.create(content_object=contact, user=self.user)

        log_entry = TimelineLog.objects.last()
        action = CustomTimelineLogAdmin.get_action_flag(
            CustomTimelineLogAdmin, log_entry
        )
        self.assertEquals(action, "")


class TestTimelineLogExport(WebTest):
    @freeze_time("2021-10-18 13:00:00")
    def test_proper_data_is_exported(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        log_entry = TimelineLog.objects.create(content_object=user, user=user)
        form = self.app.get(
            reverse("admin:timeline_logger_timelinelog_export"), user=user
        ).forms[0]

        # csv format chosen
        form["file_format"] = "0"
        response = form.submit()
        exported_data = response.content.decode("utf-8").replace("\r\n", "").split(",")

        self.assertEqual(
            exported_data,
            [
                "extra_data",
                "id",
                "content_type",
                "object_id",
                "timestamp",
                "user",
                "template",
                str(log_entry.id),
                str(log_entry.content_type_id),
                str(user.id),
                "2021-10-18 15:00:00",
                str(user.id),
                "timeline_logger/default.txt",
            ],
        )
