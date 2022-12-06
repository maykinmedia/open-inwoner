from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import ActionFactory, UserFactory

from ...plans.tests.factories import PlanFactory
from ..models import SiteConfiguration


class TestShowPlans(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.config = SiteConfiguration.get_solo()

        self.plan = PlanFactory(created_by=self.user)
        self.action = ActionFactory(created_by=self.user, plan=self.plan)

        self.plan_list_url = reverse("plans:plan_list")

    def test_default_enabled(self):
        self.assertTrue(self.config.show_plans)

    def test_when_enabled_and_user_is_logged_in(self):
        response = self.app.get(reverse("root"), user=self.user)

        navigations = response.pyquery(".primary-navigation")
        self.assertEqual(len(navigations), 2)
        for elt in navigations.items():
            self.assertNotEqual(elt.find(f'a[href="{self.plan_list_url}"]'), [])

        grid = response.pyquery(".grid")
        self.assertNotEqual(grid.find(".plans-cards"), [])
        self.assertNotEqual(grid.find(f'a[href="{self.plan_list_url}"]'), [])

    def test_when_enabled_and_user_is_not_logged_in(self):
        response = self.app.get(reverse("root"))

        navigations = response.pyquery(".primary-navigation")
        self.assertEqual(len(navigations), 2)
        for elt in navigations.items():
            self.assertEqual(elt.find(f'a[href="{self.plan_list_url}"]'), [])

        grid = response.pyquery(".grid")
        self.assertEqual(grid.find(".plans-cards"), [])
        self.assertEqual(grid.find(f'a[href="{self.plan_list_url}"]'), [])

    def test_when_disabled_and_user_is_logged_in(self):
        self.config.show_plans = False
        self.config.save()
        response = self.app.get(reverse("root"), user=self.user)

        navigations = response.pyquery(".primary-navigation")
        self.assertEqual(len(navigations), 2)
        for elt in navigations.items():
            self.assertEqual(elt.find(f'a[href="{self.plan_list_url}"]'), [])

        grid = response.pyquery(".grid")
        self.assertEqual(grid.find(".plans-cards"), [])
        self.assertEqual(grid.find(f'a[href="{self.plan_list_url}"]'), [])

    def test_when_disabled_and_user_is_not_logged_in(self):
        self.config.show_plans = False
        self.config.save()
        response = self.app.get(reverse("root"))

        navigations = response.pyquery(".primary-navigation")
        self.assertEqual(len(navigations), 2)
        for elt in navigations.items():
            self.assertEqual(elt.find(f'a[href="{self.plan_list_url}"]'), [])

        grid = response.pyquery(".grid")
        self.assertEqual(grid.find(".plans-cards"), [])
        self.assertEqual(grid.find(f'a[href="{self.plan_list_url}"]'), [])

    def test_plan_pages_show_404_when_disabled(self):
        urls = [
            reverse("plans:plan_list"),
            reverse("plans:plan_create"),
            reverse("plans:plan_detail", kwargs={"uuid": self.plan.uuid}),
            reverse("plans:plan_edit", kwargs={"uuid": self.plan.uuid}),
            reverse("plans:plan_edit_goal", kwargs={"uuid": self.plan.uuid}),
            reverse("plans:plan_add_file", kwargs={"uuid": self.plan.uuid}),
            reverse("plans:plan_export", kwargs={"uuid": self.plan.uuid}),
            reverse("plans:plan_action_create", kwargs={"uuid": self.plan.uuid}),
            reverse(
                "plans:plan_action_edit",
                kwargs={"plan_uuid": self.plan.uuid, "uuid": self.action.uuid},
            ),
            reverse(
                "plans:plan_action_delete",
                kwargs={"plan_uuid": self.plan.uuid, "uuid": self.action.uuid},
            ),
        ]

        # test disabled raises http 404
        self.config.show_plans = False
        self.config.save()

        for url in urls:
            with self.subTest(f"hide anon {url}"):
                self.app.get(url, status=404)

        for url in urls:
            with self.subTest(f"hide authenticated {url}"):
                self.app.get(url, status=404, user=self.user)
