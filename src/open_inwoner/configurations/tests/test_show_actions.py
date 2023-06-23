from django.test import override_settings
from django.urls import reverse

from cms import api
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import ActionFactory, UserFactory
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestShowActions(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.action = ActionFactory(created_by=self.user)
        self.profile_url = reverse("profile:detail")
        self.actions_list_url = reverse("profile:action_list")

        # cms profile apphook configuration
        self.profile_config = ProfileConfig.objects.create(namespace="profile")
        api.create_page(
            "profile",
            "INHERIT",
            "nl",
            published=True,
            apphook="ProfileApphook",
            apphook_namespace=self.profile_config.namespace,
        )

    def test_default_enabled(self):
        self.assertTrue(self.profile_config.actions)

    def test_when_enabled_and_user_is_logged_in(self):
        response = self.app.get(self.profile_url, user=self.user)

        links = response.pyquery(".personal-overview")
        self.assertNotEqual(links.find(".personal-overview__actions"), [])
        self.assertNotEqual(links.find(f'a[href="{self.actions_list_url}"]'), [])

    def test_when_disabled_and_user_is_logged_in(self):
        self.profile_config.actions = False
        self.profile_config.save()
        response = self.app.get(self.profile_url, user=self.user)

        links = response.pyquery(".personal-overview")
        self.assertEqual(links.find(".personal-overview__actions"), [])
        self.assertEqual(links.find(f'a[href="{self.actions_list_url}"]'), [])

    def test_action_pages_show_404_when_disabled(self):
        urls = [
            reverse("profile:action_list"),
            reverse("profile:action_create"),
            reverse("profile:action_list_export"),
            reverse("profile:action_edit", kwargs={"uuid": self.action.uuid}),
            reverse("profile:action_delete", kwargs={"uuid": self.action.uuid}),
            reverse("profile:action_export", kwargs={"uuid": self.action.uuid}),
            reverse("profile:action_download", kwargs={"uuid": self.action.uuid}),
            reverse("profile:action_history", kwargs={"uuid": self.action.uuid}),
        ]

        # test disabled raises http 404
        self.profile_config.actions = False
        self.profile_config.save()

        for url in urls:
            with self.subTest(f"{url}"):
                self.app.get(url, status=404, user=self.user)
