from django.test import TestCase
from django.urls import reverse_lazy


class KvKViewsTestCase(TestCase):
    url = reverse_lazy("kvk:branches")

    def test_get_branches_page_without_kvk_throws_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_post_branches_page_without_kvk_unauthenticated_throws_401(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 401)
