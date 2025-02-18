from django.test import TestCase, override_settings
from django.urls import reverse

from pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.configurations.models import SiteConfiguration


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ContextProcessorTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_robots_indexing(self):
        url = reverse("profile:detail")

        self.client.force_login(self.user)

        test_cases = [(True, "all"), (False, "noindex")]
        for enable_crawler_indexing, expected_result in test_cases:
            with self.subTest(enable_crawler_indexing=enable_crawler_indexing):
                config = SiteConfiguration.get_solo()
                config.enable_crawler_indexing = enable_crawler_indexing
                config.save()

                response = self.client.get(url)

                doc = PyQuery(response.content)

                robots_content = doc('meta[name="robots"]').attr("content")

                self.assertEqual(robots_content, expected_result)
