import os
from unittest.mock import patch

from django.core.checks import Warning
from django.test import SimpleTestCase

from open_inwoner.utils.checks import (
    REMOVED_NOTIFICATION_THROTTLE_SETTINGS,
    check_removed_notification_throttle_settings,
)


class CheckRemovedNotificationThrottleSettingsTests(SimpleTestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ))
        for name in REMOVED_NOTIFICATION_THROTTLE_SETTINGS:
            os.environ.pop(name, None)

    def test_warns_about_each_removed_setting_that_is_set(self):
        os.environ["CACHE_NOTIFICATION_THROTTLE_CLIENT_CLASS"] = (
            "django_redis.client.DefaultClient"
        )
        os.environ["CACHE_NOTIFICATION_THROTTLE_IGNORE_EXCEPTIONS"] = "False"

        self.assertEqual(
            check_removed_notification_throttle_settings(None),
            [
                Warning(
                    f"{name} is set, but is no longer used.",
                    hint=(
                        "The cache used to rate limit notifications is always a "
                        "Redis cache with the same settings as the default cache; "
                        "only its location can be set, with "
                        f"CACHE_NOTIFICATION_THROTTLE_LOCATION. Remove {name} from "
                        "the configuration."
                    ),
                    id="utils.W002",
                )
                for name in (
                    "CACHE_NOTIFICATION_THROTTLE_CLIENT_CLASS",
                    "CACHE_NOTIFICATION_THROTTLE_IGNORE_EXCEPTIONS",
                )
            ],
        )

    def test_no_warning_when_only_the_location_is_set(self):
        os.environ["CACHE_NOTIFICATION_THROTTLE_LOCATION"] = "redis://redis:6379/3"

        self.assertEqual(check_removed_notification_throttle_settings(None), [])
