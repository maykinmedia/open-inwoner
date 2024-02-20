from django.urls import reverse

from django_webtest import WebTest
from freezegun import freeze_time

from open_inwoner.utils.test import ClearCachesMixin


class PasswordResetViewTests(ClearCachesMixin, WebTest):
    """
    Freeze the time to ensure a consistent cache key for throttling

    Because the cachingmixin uses `time()` to generate a cache key,
    if `time()` for instance is about to reach a value where `% 60` equals zero, the
    cache key changes, meaning that the throttling essentially resets for that IP.

    >>> 1708335959 - (1708335959 % 60)
    1708335900
    >>> 335960 1708335960 - (1708335960 % 60)
    1708335960
    """

    @freeze_time("2024-01-01T12:00:00")
    def test_user_cant_access_the_password_reset_view_more_than_5_times(self):
        url = reverse("admin_password_reset")
        self.app.get(url, status=200)

        for i in range(10):
            self.app.get(url, status=(200, 403))

        self.app.get(url, status=403)
