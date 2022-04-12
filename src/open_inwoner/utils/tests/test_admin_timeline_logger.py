from datetime import datetime

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from freezegun import freeze_time
from timeline_logger.models import TimelineLog

from open_inwoner.accounts.models import Contact
from open_inwoner.accounts.tests.factories import ContactFactory, UserFactory
from open_inwoner.accounts.views import contacts


class TestAdditionTimelineLogging(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)

    @freeze_time("2021-10-18 13:00:00")
    def test_added_object_is_logged(self):
        contact = ContactFactory.build()
        url = reverse("admin:accounts_contact_add")
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = contact.first_name
        form["last_name"] = contact.last_name
        form["email"] = contact.email
        form["created_by"] = self.user.id
        form.submit()
        log_entry = TimelineLog.objects.first()
        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Contact.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("Toegevoegd."),
                "action_flag": 1,
                "content_object_repr": contact.get_name(),
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
        log_entry = TimelineLog.objects.first()
        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(log_entry.content_object.id, Contact.objects.first().id)
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": _("Voornaam en Aangemaakt door gewijzigd."),
                "action_flag": 2,
                "content_object_repr": f"Vasileios {contact.last_name}",
            },
        )

    @freeze_time("2021-10-18 13:00:00")
    def test_deleted_object_is_logged(self):
        contact = ContactFactory()
        url = reverse("admin:accounts_contact_delete", kwargs={"object_id": contact.id})
        delete_form = self.app.get(url, user=self.user).forms[0]
        delete_form.submit()
        log_entry = TimelineLog.objects.first()
        self.assertEquals(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEquals(
            log_entry.extra_data,
            {
                "message": "",
                "action_flag": 3,
                "content_object_repr": contact.get_name(),
            },
        )
