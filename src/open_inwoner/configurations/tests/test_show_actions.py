from django.core.exceptions import ValidationError
from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import ActionFactory, UserFactory

from ...plans.tests.factories import PlanFactory
from ..models import SiteConfiguration


class TestShowActions(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.config = SiteConfiguration.get_solo()

        self.action = ActionFactory(created_by=self.user)

        self.profile_url = reverse("accounts:my_profile")
        self.actions_list_url = reverse("accounts:action_list")

    def test_default_enabled(self):
        self.assertTrue(self.config.show_actions)

    def test_show_plans_requires_show_actions(self):
        config = SiteConfiguration.get_solo()

        # fine
        config.show_plans = False
        config.show_actions = False
        config.clean()

        # fine
        config.show_plans = True
        config.show_actions = True
        config.clean()

        # fine
        config.show_plans = False
        config.show_actions = True
        config.clean()

        # not fine
        config.show_plans = True
        config.show_actions = False
        with self.assertRaises(ValidationError) as e:
            config.clean()

        self.assertEqual(
            set(e.exception.error_dict.keys()), {"show_actions", "show_plans"}
        )

    def test_when_enabled_and_user_is_logged_in(self):
        response = self.app.get(self.profile_url, user=self.user)

        links = response.pyquery(".personal-overview")
        self.assertNotEqual(links.find(".personal-overview__actions"), [])
        self.assertNotEqual(links.find(f'a[href="{self.actions_list_url}"]'), [])

    def test_when_disabled_and_user_is_logged_in(self):
        self.config.show_actions = False
        self.config.save()
        response = self.app.get(self.profile_url, user=self.user)

        links = response.pyquery(".personal-overview")
        self.assertEqual(links.find(".personal-overview__actions"), [])
        self.assertEqual(links.find(f'a[href="{self.actions_list_url}"]'), [])

    def test_action_pages_show_404_when_disabled(self):
        urls = [
            reverse("accounts:action_list"),
            reverse("accounts:action_create"),
            reverse("accounts:action_list_export"),
            reverse("accounts:action_edit", kwargs={"uuid": self.action.uuid}),
            reverse("accounts:action_delete", kwargs={"uuid": self.action.uuid}),
            reverse("accounts:action_export", kwargs={"uuid": self.action.uuid}),
            reverse("accounts:action_download", kwargs={"uuid": self.action.uuid}),
            reverse("accounts:action_history", kwargs={"uuid": self.action.uuid}),
        ]

        # test disabled raises http 404
        self.config.show_actions = False
        self.config.save()

        for url in urls:
            with self.subTest(f"{url}"):
                self.app.get(url, status=404, user=self.user)
