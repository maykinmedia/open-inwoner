from datetime import date
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from playwright.sync_api import expect
from privates.test import temp_private_root

from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.tests.playwright import get_driver_name

from ...utils.tests.playwright import PlaywrightSyncLiveServerTestCase
from ..choices import StatusChoices
from ..models import Action
from .factories import ActionFactory, DigidUserFactory, UserFactory


@temp_private_root()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ActionViewTests(WebTest):
    def setUp(self) -> None:
        # cookiebanner
        self.config = SiteConfiguration.get_solo()
        cms_tools.create_homepage()
        self.config.cookie_info_text = ""
        self.config.save()

        self.user = UserFactory()
        self.action = ActionFactory(
            name="action_that_should_be_found",
            created_by=self.user,
            file=SimpleUploadedFile("file.txt", b"test content"),
        )
        self.action_deleted = ActionFactory(
            name="action_that_was_deleted",
            created_by=self.user,
            is_deleted=True,
        )

        self.login_url = reverse("login")
        self.list_url = reverse("profile:action_list")
        self.edit_url = reverse(
            "profile:action_edit", kwargs={"uuid": self.action.uuid}
        )
        self.edit_status_url = reverse(
            "profile:action_edit_status", kwargs={"uuid": self.action.uuid}
        )
        self.delete_url = reverse(
            "profile:action_delete", kwargs={"uuid": self.action.uuid}
        )
        self.create_url = reverse("profile:action_create")
        self.export_url = reverse(
            "profile:action_export", kwargs={"uuid": self.action.uuid}
        )
        self.export_list_url = reverse("profile:action_list_export")
        self.download_url = reverse(
            "profile:action_download", kwargs={"uuid": self.action.uuid}
        )
        self.history_url = reverse(
            "profile:action_history", kwargs={"uuid": self.action.uuid}
        )

    def test_queryset_visible(self):
        self.assertEqual(list(Action.objects.visible()), [self.action])

    def test_action_list_login_required(self):
        response = self.app.get(self.list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.list_url}")

    def test_action_list_filled(self):
        response = self.app.get(self.list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.action.name)
        self.assertEqual(list(response.context["actions"]), [self.action])

    def test_action_list_filter_is_for(self):
        user = UserFactory()
        action = ActionFactory(
            created_by=self.user,
            status=StatusChoices.closed,
            end_date=date.today(),
            is_for=user,
        )
        action2 = ActionFactory(
            end_date="2021-04-02", status=StatusChoices.open, is_for=self.user
        )
        self.assertNotEqual(action.is_for_id, self.user.id)
        response = self.app.get(
            f"{self.list_url}?is_for={self.user.id}", user=self.user
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["actions"]), [action2, self.action])

    def test_action_list_filter_status(self):
        action = ActionFactory(
            created_by=self.user, status=StatusChoices.closed, end_date=date.today()
        )
        action2 = ActionFactory(
            end_date="2021-04-02", status=StatusChoices.open, is_for=self.user
        )
        response = self.app.get(
            f"{self.list_url}?status={StatusChoices.open}", user=self.user
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["actions"]), [action2, self.action])

    def test_action_list_filter_end_date(self):
        action = ActionFactory(
            created_by=self.user, status=StatusChoices.closed, end_date=date.today()
        )
        action2 = ActionFactory(
            end_date="2021-04-02", status=StatusChoices.open, is_for=self.user
        )
        response = self.app.get(f"{self.list_url}?end_date=02-04-2021", user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["actions"]), [action2])

    def test_action_list_only_show_personal_actions(self):
        other_user = UserFactory()
        response = self.app.get(self.list_url, user=other_user)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.action.name)
        self.assertEqual(list(response.context["actions"]), [])

    def test_action_edit_login_required(self):
        response = self.app.get(self.edit_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.edit_url}")

    def test_action_edit(self):
        response = self.app.get(self.edit_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.action.name)

    def test_action_edit_not_your_action(self):
        other_user = UserFactory()
        self.app.get(self.edit_url, user=other_user, status=404)

    def test_action_edit_deleted_action(self):
        url = reverse("profile:action_edit", kwargs={"uuid": self.action_deleted.uuid})
        self.app.get(url, user=self.user, status=404)

    def test_action_delete_login_required(self):
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)

    def test_action_delete_http_get_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 405)

    def test_action_delete(self):
        self.client.force_login(self.user)
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.list_url)

        # Action is now marked as .is_deleted (and not actually deleted)
        action = Action.objects.get(id=self.action.id)
        self.assertTrue(action.is_deleted)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        expected = _("Actie '{action}' is verwijdered.").format(action=self.action)
        self.assertEqual(str(messages[0]), expected)

    def test_action_delete_not_your_action(self):
        other_user = UserFactory()
        self.client.force_login(other_user)
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 404)

    def test_action_create_login_required(self):
        response = self.app.get(self.create_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.create_url}")

    def test_action_export(self):
        response = self.app.get(self.export_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/pdf")
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="action_{self.action.uuid}.pdf"',
        )

    def test_action_export_login_required(self):
        response = self.app.get(self.export_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.export_url}")

    def test_action_export_not_your_action(self):
        other_user = UserFactory()
        self.app.get(self.export_url, user=other_user, status=404)

    def test_action_export_deleted_action(self):
        url = reverse(
            "profile:action_export", kwargs={"uuid": self.action_deleted.uuid}
        )
        self.app.get(url, user=self.user, status=404)

    def test_action_list_export(self):
        response = self.app.get(self.export_list_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/pdf")
        self.assertEqual(
            response["Content-Disposition"], 'attachment; filename="actions.pdf"'
        )
        self.assertEqual(list(response.context["actions"]), [self.action])

    def test_action_list_export_login_required(self):
        response = self.app.get(self.export_list_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.export_list_url}")

    def test_action_download_file(self):
        response = self.app.get(self.download_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/plain")
        self.assertEqual(response.content, b"test content")

    def test_action_download_login_required(self):
        response = self.app.get(self.download_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.download_url}")

    def test_action_download_not_your_action(self):
        other_user = UserFactory()
        self.app.get(self.download_url, user=other_user, status=403)

    def test_action_download_deleted_action(self):
        url = reverse(
            "profile:action_download", kwargs={"uuid": self.action_deleted.uuid}
        )
        self.app.get(url, user=self.user, status=404)

    def test_action_history(self):
        response = self.app.get(self.history_url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.action.name)

    def test_action_history_breadcrumbs(self):
        response = self.app.get(self.history_url, user=self.user)
        crumbs = response.pyquery(".breadcrumbs__list-item")
        self.assertIn(_("Mijn profiel"), crumbs[1].text_content())
        self.assertIn(_("Mijn acties"), crumbs[2].text_content())

    def test_action_history_not_your_action(self):
        other_user = UserFactory()
        self.app.get(self.history_url, user=other_user, status=404)

    def test_action_history_login_required(self):
        response = self.app.get(self.history_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.history_url}")

    def test_action_history_deleted_action(self):
        url = reverse(
            "profile:action_history", kwargs={"uuid": self.action_deleted.uuid}
        )
        self.app.get(url, user=self.user, status=404)

    def test_action_status(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.edit_status_url,
            {"status": StatusChoices.closed},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.action.refresh_from_db()
        self.assertEqual(self.action.status, StatusChoices.closed)

    def test_action_status_requires_htmx_header(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.edit_status_url,
            {"status": StatusChoices.closed},
        )
        self.assertEqual(response.status_code, 400)

    def test_action_status_invalid_post_data(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.edit_status_url,
            {"not_the_parameter": 123},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 400)

    def test_action_status_http_get_disallowed(self):
        self.client.force_login(self.user)
        response = self.client.get(
            self.edit_status_url,
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 405)

    def test_action_status_login_required(self):
        response = self.client.post(
            self.edit_status_url,
            {"status": StatusChoices.closed},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 403)

    def test_action_status_not_your_action(self):
        other_user = UserFactory()
        self.client.force_login(other_user)
        response = self.client.post(
            self.edit_status_url,
            {"status": StatusChoices.closed},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 404)


@tag("e2e")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@patch("open_inwoner.configurations.models.SiteConfiguration.get_solo")
class ActionsPlaywrightTests(PlaywrightSyncLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = DigidUserFactory.create()
        # let's reuse the login storage_state
        cls.user_login_state = cls.get_user_bsn_login_state(cls.user)

    def setUp(self) -> None:
        super().setUp()

        self.action = ActionFactory(
            name="my_action",
            created_by=self.user,
            status=StatusChoices.open,
        )
        self.action_list_url = reverse("profile:action_list")

    def test_action_status(self, mock_solo):
        # @skipIf(...) causes issues together with Playwright
        if get_driver_name() == "firefox":
            self.skipTest("Test is flakey in firefox")

        mock_solo.return_value.cookiebanner_enabled = False

        context = self.browser.new_context(storage_state=self.user_login_state)

        page = context.new_page()
        page.goto(self.live_reverse("profile:action_list"))

        # find action element and the dropdown widget
        action_element = page.locator(f"#actions_{self.action.id}__status")
        dropdown_button = action_element.locator(".actions__status-selector")
        dropdown_content = action_element.locator(".dropdown__content")

        # labels are lazy; force evaluation by casting to `str`
        approval_label = str(StatusChoices.approval.label)
        closed_label = str(StatusChoices.closed.label)
        open_label = str(StatusChoices.open.label)

        expect(dropdown_button).to_contain_text(open_label)
        # grab buttons
        status_closed_button = dropdown_content.get_by_role("button", name=closed_label)
        status_approval_button = dropdown_content.get_by_role(
            "button", name=approval_label
        )
        expect(status_approval_button).to_be_visible(visible=False)

        # open dropdown widget
        dropdown_button.click()
        expect(status_approval_button).to_be_visible()

        # click on status-closed button
        status_approval_button.click()

        # status should change to approval
        expect(dropdown_button).to_contain_text(approval_label)

        # dropdown widget is closed
        expect(status_approval_button).to_be_visible(visible=False)

        # check database
        self.action.refresh_from_db()
        self.assertEqual(self.action.status, StatusChoices.approval)

        # open dropdown again to see if the dropdown got re-hydrated
        dropdown_button.click()
        expect(status_closed_button).to_be_visible()

        # click on status-closed button
        status_closed_button.click()

        # status should change
        expect(dropdown_button).to_contain_text(closed_label)

        # dropdown widget is closed
        expect(status_closed_button).to_be_visible(visible=False)

        # check database
        self.action.refresh_from_db()
        self.assertEqual(self.action.status, StatusChoices.closed)
