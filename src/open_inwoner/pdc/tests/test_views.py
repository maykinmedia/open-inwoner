from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.configurations.models import SiteConfiguration

from .factories import CategoryFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestCategoryListView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user.set_password("12345")
        cls.user.email = "test@email.com"
        cls.user.save()

    def test_access_restricted(self):
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

    def test_access_not_restricted(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        url = reverse("products:category_list")

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestCategoryDetailView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.user.set_password("12345")
        cls.user.email = "test@email.com"
        cls.user.save()

        cls.category = CategoryFactory.create(name="test cat")

    def test_access_restricted(self):
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

    def test_access_not_restricted(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        url = reverse("products:category_detail", kwargs={"slug": self.category.slug})

        # request with anonymous user
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
