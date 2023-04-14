import logging
from datetime import timedelta

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest
from freezegun import freeze_time
from privates.test import temp_private_root
from timeline_logger.models import TimelineLog
from webtest import Upload

from open_inwoner.accounts.models import Invite
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.tests.factories import CategoryFactory
from open_inwoner.utils.logentry import LOG_ACTIONS

from ..choices import LoginTypeChoices, StatusChoices
from ..forms import ActionForm
from ..models import Action, Document, Message, User
from .factories import (
    ActionFactory,
    DocumentFactory,
    InviteFactory,
    MessageFactory,
    UserFactory,
)


@freeze_time("2021-10-18 13:00:00")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestProfile(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()

        self.config = SiteConfiguration.get_solo()
        self.config.login_allow_registration = True
        self.config.save()

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
        log_entry = TimelineLog.objects.get()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        user = User.objects.get(email=user.email)
        self.assertEqual(log_entry.content_object.id, user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user was created"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": user.email,
            },
        )

    def test_users_modification_is_logged(self):
        form = self.app.get(reverse("profile:edit"), user=self.user).forms[
            "profile-edit"
        ]
        form["first_name"] = "Updated name"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("profile was modified"),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": self.user.email,
            },
        )

    def test_categories_modification_is_logged(self):
        CategoryFactory()
        CategoryFactory()
        form = self.app.get(reverse("profile:categories"), user=self.user).forms[
            "change-categories"
        ]

        form.get("selected_categories", index=1).checked = True
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("categories were modified"),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": self.user.email,
            },
        )

    def test_user_notifications_update_is_logged(self):
        form = self.app.get(reverse("accounts:my_notifications"), user=self.user).forms[
            "change-notifications"
        ]
        form["messages_notifications"] = False
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("users notifications were modified"),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": self.user.email,
            },
        )

    def test_login_via_admin_is_logged(self):
        self.app.post(reverse("admin:login"), user=self.user)
        log_entry = TimelineLog.objects.get()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user was logged in via admin page"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    def test_login_via_frontend_using_email_is_logged(self):
        self.app.post(reverse("login"), user=self.user)
        log_entry = TimelineLog.objects.get()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user was logged in via frontend using email"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    def test_login_via_frontend_using_digid_is_logged(self):
        user = UserFactory(login_type=LoginTypeChoices.digid)
        self.app.get(reverse("digid:acs"), {"bsn": "123123222"}, user=user)
        log_entry = TimelineLog.objects.first()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user was logged in via frontend using digid"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": user.email,
            },
        )

    def test_logout_is_logged(self):
        self.app.get(reverse("logout"), user=self.user)
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user was logged out"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    def test_users_deactivation_is_logged(self):
        form = self.app.get(reverse("profile:detail"), user=self.user).forms[
            "deactivate-form"
        ]
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user was deactivated via frontend"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    def test_password_change_is_logged(self):
        user = UserFactory(password="test")
        form = self.app.get(reverse("password_change"), user=user).forms[
            "password-change-form"
        ]
        form["old_password"] = "test"
        form["new_password1"] = "newPassw0rd"
        form["new_password2"] = "newPassw0rd"
        form.submit(status=302)

        log_entry = TimelineLog.objects.filter(
            extra_data__message=str(_("password was changed"))
        ).last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("password was changed"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": user.email,
            },
        )

    def test_password_reset_access_is_logged(self):
        form = self.app.get(reverse("password_reset")).forms["password-reset-form"]
        form["email"] = self.user.email
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("password reset was accessed"),
                "log_level": logging.INFO,
                "action_flag": list(LOG_ACTIONS[5]),
                "content_object_repr": "",
            },
        )

    def test_password_reset_confirm_is_logged(self):
        form = self.app.get(reverse("password_reset")).forms["password-reset-form"]
        form["email"] = self.user.email
        response = form.submit()

        token = response.context[0]["token"]
        uid = response.context[0]["uid"]
        confirm_response = self.app.get(
            reverse("password_reset_confirm", kwargs={"token": token, "uidb64": uid})
        ).follow()
        form = confirm_response.forms["password-reset-confirm"]
        form["new_password1"] = "passW0rd@"
        form["new_password2"] = "passW0rd@"
        form.submit()

        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("password reset was completed"),
                "log_level": logging.INFO,
                "action_flag": list(LOG_ACTIONS[5]),
                "content_object_repr": self.user.email,
            },
        )


@freeze_time("2021-10-18 13:00:00")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestInvites(WebTest):
    def setUp(self):
        self.invitee = UserFactory(is_active=False)

    def test_accepted_invite_is_logged(self):
        invite = InviteFactory(invitee=self.invitee)
        url = invite.get_absolute_url()

        form = self.app.get(url).forms["invite-form"]
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.invitee.id, self.invitee.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("invitation accepted"),
                "log_level": logging.INFO,
                "action_flag": list(LOG_ACTIONS[5]),
                "content_object_repr": _("For: {invitee} (2021-10-18)").format(
                    invitee=self.invitee.email
                ),
            },
        )

    def test_expired_invite_is_logged(self):
        invite = InviteFactory.create(invitee=self.invitee)
        invite.created_on = timezone.now() - timedelta(days=30)
        invite.save()
        url = invite.get_absolute_url()

        response = self.app.get(url, status=404)

        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.invitee.id, self.invitee.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("invitation expired"),
                "log_level": logging.INFO,
                "action_flag": list(LOG_ACTIONS[5]),
                "content_object_repr": _("For: {invitee} (2021-09-18)").format(
                    invitee=self.invitee.email
                ),
            },
        )


@freeze_time("2021-10-18 13:00:00")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestContacts(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()
        self.contact = UserFactory()
        self.user.user_contacts.add(self.contact)

    def test_new_contact_invite_is_logged(self):
        form = self.app.get(reverse("profile:contact_create"), user=self.user).forms[
            "contact-form"
        ]
        form["email"] = "user@example.com"
        form["first_name"] = "Koe"
        form["last_name"] = "Kilsor"
        form.submit()
        log_entry = TimelineLog.objects.last()
        invite = Invite.objects.get(invitee_email="user@example.com")

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, invite.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("invite was created"),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": str(invite),
            },
        )

    def test_existing_user_contact_approval_is_logged(self):
        existing_user = UserFactory()
        form = self.app.get(reverse("profile:contact_create"), user=self.user).forms[
            "contact-form"
        ]
        form["email"] = existing_user.email
        form["first_name"] = existing_user.first_name
        form["last_name"] = existing_user.last_name
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, existing_user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("contact was added, pending approval"),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": str(existing_user),
            },
        )

    def test_contact_removal_is_logged(self):
        self.app.post(
            reverse("profile:contact_delete", kwargs={"uuid": self.contact.uuid}),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.object_id, str(self.contact.id))
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("contact relationship was removed"),
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": str(self.contact),
            },
        )


@freeze_time("2021-10-18 13:00:00")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestDocuments(WebTest):
    csrf_checks = False

    def setUp(self):
        self.user = UserFactory()
        self.document = DocumentFactory(owner=self.user)

    def test_document_download_is_logged(self):
        self.app.get(
            reverse("profile:documents_download", kwargs={"uuid": self.document.uuid}),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.document.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("file was downloaded"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.document.name,
            },
        )

    @temp_private_root()
    def test_document_deletion_is_logged(self):
        self.app.post(
            reverse("profile:documents_delete", kwargs={"uuid": self.document.uuid}),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.object_id, str(self.document.id))
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("file was deleted"),
                "action_flag": list(LOG_ACTIONS[DELETION]),
                "content_object_repr": self.document.name,
            },
        )


@freeze_time("2021-10-18 13:00:00")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestActions(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.action = ActionFactory(created_by=self.user)

    def test_action_addition_is_logged(self):
        action = ActionFactory.build(created_by=self.user)
        form = self.app.get(reverse("profile:action_create"), user=self.user).forms[
            "action-create"
        ]
        form["name"] = action.name
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, Action.objects.all()[1].id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("action was created"),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": action.name,
            },
        )

    def test_action_single_field_update_is_logged(self):
        form = self.app.get(
            reverse("profile:action_edit", kwargs={"uuid": self.action.uuid}),
            user=self.user,
        ).forms["action-create"]
        form["name"] = "Updated name"
        form.submit()

        updated_action = Action.objects.get(uuid=self.action.uuid)
        name_label = ActionForm.base_fields["name"].label
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.action.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": [
                    _("{label} changed to {updated_data}.").format(
                        label=name_label, updated_data=updated_action.name
                    )
                ],
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": "Updated name",
            },
        )

    def test_action_multiple_fields_update_is_logged(self):
        form = self.app.get(
            reverse("profile:action_edit", kwargs={"uuid": self.action.uuid}),
            user=self.user,
        ).forms["action-create"]
        form["name"] = "Updated name"
        form["status"] = StatusChoices.approval
        form.submit()

        updated_action = Action.objects.get(uuid=self.action.uuid)
        name_label = ActionForm.base_fields["name"].label
        status_label = ActionForm.base_fields["status"].label
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.action.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": [
                    _("{name_label} changed to {updated_name}.").format(
                        name_label=name_label, updated_name=updated_action.name
                    ),
                    _("{status_label} changed to {updated_status}.").format(
                        status_label=status_label,
                        updated_status=updated_action.get_status_display(),
                    ),
                ],
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": "Updated name",
            },
        )

    def test_action_status_toggle_is_logged(self):
        edit_status_url = reverse(
            "profile:action_edit_status", kwargs={"uuid": self.action.uuid}
        )
        self.client.force_login(self.user)
        response = self.client.post(
            edit_status_url,
            {"status": StatusChoices.closed},
            HTTP_HX_REQUEST="true",
        )

        updated_action = Action.objects.get(uuid=self.action.uuid)
        status_label = ActionForm.base_fields["status"].label
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.action.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": [
                    _("{status_label} changed to {updated_status}.").format(
                        status_label=status_label,
                        updated_status=updated_action.get_status_display(),
                    )
                ],
                "action_flag": list(LOG_ACTIONS[CHANGE]),
                "content_object_repr": str(self.action),
            },
        )


@freeze_time("2021-10-18 13:00:00")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestMessages(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.user.user_contacts.add(self.other_user)

    def test_created_message_action_from_contacts_is_logged(self):
        response = self.app.get(
            reverse("inbox:index", kwargs={"uuid": self.other_user.uuid}),
            user=self.user,
            auto_follow=True,
        )
        form = response.forms["message-form"]
        form["content"] = "some content"
        form.submit()
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, Message.objects.get().id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("message was created"),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": _("From: {me}, To: {other} (2021-10-18)").format(
                    me=self.user.email, other=self.other_user.email
                ),
            },
        )

    def test_created_message_action_from_start_is_logged(self):
        response = self.app.get(
            reverse("inbox:start"),
            user=self.user,
        )
        form = response.forms["start-message-form"]
        form["receiver"] = str(self.other_user.uuid)
        form["content"] = "some content"
        form.submit()
        log_entry = TimelineLog.objects.last()
        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, Message.objects.get().id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("message was created"),
                "action_flag": list(LOG_ACTIONS[ADDITION]),
                "content_object_repr": _("From: {me}, To: {other} (2021-10-18)").format(
                    me=self.user.email, other=self.other_user.email
                ),
            },
        )

    @temp_private_root()
    def test_download_file_from_messages_is_logged(self):
        message = MessageFactory(
            file=SimpleUploadedFile("file.txt", b"test content"),
        )
        download_url = reverse("inbox:download", args=[message.uuid])
        self.app.get(download_url, user=message.receiver)
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, message.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("file was downloaded"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": _(
                    "From: {sender}, To: {receiver} (2021-10-18)"
                ).format(sender=message.sender, receiver=message.receiver),
            },
        )


@freeze_time("2021-10-18 13:00:00")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestExport(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.action1 = ActionFactory(created_by=self.user)
        self.action2 = ActionFactory(created_by=self.user)

    def test_profile_export_is_logged(self):
        self.app.get(reverse("profile:export"), user=self.user)
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("file profile.pdf was exported"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    def test_action_export_is_logged(self):
        self.app.get(
            reverse("profile:action_export", kwargs={"uuid": self.action1.uuid}),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("file action_{action_uuid}.pdf was exported").format(
                    action_uuid=self.action1.uuid
                ),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    def test_action_list_export_is_logged(self):
        self.app.get(
            reverse("profile:action_list_export"),
            user=self.user,
        )
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            log_entry.timestamp.strftime("%m/%d/%Y, %H:%M:%S"), "10/18/2021, 13:00:00"
        )
        self.assertEqual(log_entry.content_object.id, self.user.id)
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("file actions.pdf was exported"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )
