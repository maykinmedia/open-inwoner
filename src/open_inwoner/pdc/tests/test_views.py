from unittest import skip

from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.configurations.models import SiteConfiguration

from .factories import CategoryFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CategoryListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user.set_password("12345")
        cls.user.email = "test@email.com"
        cls.user.save()

        cls.category1 = CategoryFactory(
            name="0001",
            visible_for_anonymous=True,
            visible_for_authenticated=True,
            visible_for_citizens=False,
            visible_for_companies=False,
        )
        cls.category2 = CategoryFactory(
            name="0002",
            visible_for_anonymous=True,
            visible_for_authenticated=False,
            visible_for_citizens=True,
            visible_for_companies=True,
        )
        cls.category3 = CategoryFactory(
            name="0003",
            visible_for_anonymous=False,
            visible_for_authenticated=True,
            visible_for_citizens=True,
            visible_for_companies=False,
        )
        cls.category4 = CategoryFactory(
            name="0004",
            visible_for_anonymous=False,
            visible_for_authenticated=False,
            visible_for_citizens=False,
            visible_for_companies=True,
        )

    def test_category_list_view_access_restricted(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = True
        config.save()

        url = reverse("products:category_list")

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/products/")

        # request with user logged in
        self.client.login(email=self.user.email, password="12345")

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
            list(response.context["object_list"]), [self.category1, self.category2]
        )

    def test_category_list_view_visibility_for_authenticated_user(self):
        url = reverse("products:category_list")

        self.client.force_login(self.user)

        # request with authenticated user
        response = self.client.get(url, user=self.user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["object_list"]), [self.category1, self.category3]
        )

    def test_category_list_view_visibility_for_digid_user(self):
        url = reverse("products:category_list")

        user = DigidUserFactory()
        self.client.force_login(user)

        # request with DigiD user
        response = self.client.get(url, user=user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["object_list"]), [self.category2, self.category3]
        )

    @skip("eHerkenning is not implemented yet")
    def test_category_list_view_visibility_for_eherkenning_user(self):
        url = reverse("products:category_list")

        # TODO should be eHerkenningUserFactory
        user = DigidUserFactory()
        self.client.force_login(user)

        # request with eHerkenning user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["object_list"]), [self.category2, self.category4]
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class CategoryDetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user.set_password("12345")
        cls.user.email = "test@email.com"
        cls.user.save()

        cls.category = CategoryFactory.create(
            name="test cat",
            description="A <em>descriptive</em> description",
            visible_for_anonymous=False,
            visible_for_authenticated=False,
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
        self.client.login(email=self.user.email, password="12345")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_category_detail_view_access_not_restricted(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        url = reverse("products:category_detail", kwargs={"slug": self.category.slug})

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_category_detail_view_access_not_restricted_if_invisible(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        url = reverse("products:category_detail", kwargs={"slug": self.category.slug})

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_category_detail_description_rendered(self):
        url = reverse("products:category_detail", kwargs={"slug": self.category.slug})

        response = self.client.get(url)

        self.assertIn(
            '<p class="p">A <em>descriptive</em> description</p>',
            response.rendered_content,
        )
        self.assertNotIn(
            '[<p class="p">A <em>descriptive</em> description</p>, <em>descriptive</em>]',
            response.rendered_content,
        )

    def test_category_breadcrumbs_404(self):
        url = reverse(
            "products:category_detail", kwargs={"slug": f"none/{self.category.slug}"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
