from django.test import TestCase
from django.urls import reverse

from open_inwoner.configurations.models import SiteConfiguration


class TestSearchView(TestCase):
    def test_search_hidden_from_anonymous_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = True
        config.save()

        response = self.client.get(reverse("search:search"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/accounts/login/?next=/search/")

    def test_search_not_hidden_from_anonymous_users(self):
        config = SiteConfiguration.get_solo()
        config.hide_categories_from_anonymous_users = False
        config.save()

        response = self.client.get(reverse("search:search"))

        self.assertEqual(response.status_code, 200)
