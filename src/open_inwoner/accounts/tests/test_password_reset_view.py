from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.utils.test import ClearCachesMixin


class PasswordResetViewTests(ClearCachesMixin, WebTest):
    def test_user_cant_access_the_password_reset_view_more_than_5_times(self):
        url = reverse("admin_password_reset")
        self.app.get(url, status=200)

        for i in range(10):
            self.app.get(url, status=(200, 403))

        self.app.get(url, status=403)
