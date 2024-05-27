from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    UserFactory,
    eHerkenningUserFactory,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.test import set_kvk_branch_number_in_session

from .factories import CategoryFactory

# Avoid redirects through `KvKLoginMiddleware`
PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CategoryListViewTest(TestCase):
    def setUp(self):
        super().setUp()

        self.category_anonymous = CategoryFactory(
            name="0001",
            visible_for_anonymous=True,
            visible_for_citizens=False,
            visible_for_companies=False,
        )
        self.category_all = CategoryFactory(
            name="0002",
            visible_for_anonymous=True,
            visible_for_citizens=True,
            visible_for_companies=True,
        )
        self.category_citizens = CategoryFactory(
            name="0003",
            visible_for_anonymous=False,
            visible_for_citizens=True,
            visible_for_companies=False,
        )
        self.category_companies = CategoryFactory(
            name="0004",
            visible_for_anonymous=False,
            visible_for_citizens=False,
            visible_for_companies=True,
        )

    def test_category_list_view_access_restricted(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = True
        config.save()

        url = reverse("products:category_list")

        user = UserFactory()

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/products/")

        # request with user logged in
        self.client.force_login(user=user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_category_list_view_access_not_restricted(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        url = reverse("products:category_list")

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_category_list_view_visibility_for_anonymous_user(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        url = reverse("products:category_list")

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["object_list"]),
            [self.category_anonymous, self.category_all],
        )

    def test_category_list_view_visibility_for_digid_user(self):
        url = reverse("products:category_list")

        user = DigidUserFactory()
        self.client.force_login(user)

        # request with DigiD user
        response = self.client.get(url, user=user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["object_list"]),
            [self.category_all, self.category_citizens],
        )

    @override_settings(MIDDLEWARE=PATCHED_MIDDLEWARE)
    def test_category_list_view_visibility_for_eherkenning_user(self):
        url = reverse("products:category_list")

        user = eHerkenningUserFactory()
        self.client.force_login(user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["object_list"]),
            [self.category_all, self.category_companies],
        )

    def test_category_list_view_visibility_for_staff_user(self):
        url = reverse("products:category_list")

        user = UserFactory(is_staff=True)
        self.client.force_login(user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["object_list"]),
            [
                self.category_anonymous,
                self.category_all,
                self.category_citizens,
                self.category_companies,
            ],
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CategoryDetailViewTest(TestCase):
    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory()

        self.category = CategoryFactory.create(
            name="test cat",
            description="A <em>descriptive</em> description",
            visible_for_anonymous=False,
        )

    def test_category_detail_view_access_restricted(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = True
        config.save()

        url = reverse("products:category_detail", kwargs={"slug": self.category.slug})

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/products/test-cat/")

        # request with user logged in
        self.client.force_login(user=self.user)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_category_detail_view_access_restricted_if_invisible(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        url = reverse("products:category_detail", kwargs={"slug": self.category.slug})

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/products/test-cat/")

    def test_category_detail_view_access_restricted_for_digid_user(self):
        category = CategoryFactory.create(
            name="test cat2",
            description="A <em>descriptive</em> description",
            visible_for_citizens=False,
        )
        user = DigidUserFactory()
        self.client.force_login(user)

        url = reverse("products:category_detail", kwargs={"slug": category.slug})

        # request with digid user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    @set_kvk_branch_number_in_session()
    def test_category_detail_view_access_restricted_for_eherkenning_user(self):
        category = CategoryFactory.create(
            name="test cat2",
            description="A <em>descriptive</em> description",
            visible_for_companies=False,
        )
        user = eHerkenningUserFactory()
        self.client.force_login(user)

        url = reverse("products:category_detail", kwargs={"slug": category.slug})

        # request with eherkenning user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)

    def test_category_detail_description_rendered(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        self.category.visible_for_anonymous = True
        self.category.save()

        url = reverse("products:category_detail", kwargs={"slug": self.category.slug})

        response = self.client.get(url)

        self.assertIn(
            "A <em>descriptive</em> description</p>",
            response.rendered_content,
        )
        self.assertNotIn(
            "[A <em>descriptive</em> description</p>, <em>descriptive</em>]",
            response.rendered_content,
        )

    def test_category_breadcrumbs_404(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        self.category.visible_for_anonymous = True
        self.category.save()

        url = reverse(
            "products:category_detail", kwargs={"slug": f"none/{self.category.slug}"}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
