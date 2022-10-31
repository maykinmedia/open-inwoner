from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse


class PasswordResetViewTests(TestCase):
    def test_user_cant_access_the_password_reset_view_more_than_5_times(self):
        url = reverse("admin_password_reset")
        cache.clear()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        for i in range(10):
            response = self.client.get(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
