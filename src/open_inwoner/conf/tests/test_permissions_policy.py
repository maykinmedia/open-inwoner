import os
from importlib import reload
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from open_inwoner.conf.app import permissions_policy as permissions_policy_settings

VIDEO = '(self "https://www.youtube.com" "https://player.vimeo.com")'


class PermissionsPolicyTests(TestCase):
    def test_policy_from_settings_is_sent(self):
        # also validates the feature names, unknown ones raise ImproperlyConfigured
        response = self.client.get(reverse("login"))

        policy = dict(
            directive.split("=", 1)
            for directive in response["Permissions-Policy"].split(", ")
        )
        self.assertEqual(
            policy,
            {
                "accelerometer": "()",
                "ambient-light-sensor": "()",
                "autoplay": VIDEO,
                "bluetooth": "()",
                "browsing-topics": "()",
                "camera": "()",
                "captured-surface-control": "()",
                "clipboard-read": "()",
                "clipboard-write": "(self)",
                "compute-pressure": "()",
                "digital-credentials-get": "()",
                "display-capture": "()",
                "encrypted-media": "()",
                "fullscreen": VIDEO,
                "gamepad": "()",
                "geolocation": "()",
                "gyroscope": "()",
                "hid": "()",
                "identity-credentials-get": "()",
                "idle-detection": "()",
                "local-fonts": "()",
                "magnetometer": "()",
                "microphone": "()",
                "midi": "()",
                "otp-credentials": "()",
                "payment": "()",
                "picture-in-picture": "()",
                "publickey-credentials-create": "(self)",
                "publickey-credentials-get": "(self)",
                "screen-wake-lock": "()",
                "serial": "()",
                "storage-access": "()",
                "usb": "()",
                "web-share": "()",
                "window-management": "()",
                "xr-spatial-tracking": "()",
            },
        )
        self.assertNotIn("Permissions-Policy-Report-Only", response)


class PermissionsPolicyReportOnlyTests(TestCase):
    def load_settings(self):
        # the env var is read when the settings module is imported
        self.addCleanup(reload, permissions_policy_settings)
        return reload(permissions_policy_settings)

    @patch.dict(os.environ, {"PERMISSIONS_POLICY_REPORT_ONLY": "true"})
    def test_report_only_mode(self):
        conf = self.load_settings()

        with override_settings(
            PERMISSIONS_POLICY=conf.PERMISSIONS_POLICY,
            PERMISSIONS_POLICY_REPORT_ONLY=conf.PERMISSIONS_POLICY_REPORT_ONLY,
        ):
            response = self.client.get(reverse("login"))

        self.assertNotIn("Permissions-Policy", response)
        self.assertIn("geolocation=()", response["Permissions-Policy-Report-Only"])

    @patch.dict(os.environ, {"PERMISSIONS_POLICY_REPORT_ONLY": "false"})
    def test_enforced_mode(self):
        conf = self.load_settings()

        with override_settings(
            PERMISSIONS_POLICY=conf.PERMISSIONS_POLICY,
            PERMISSIONS_POLICY_REPORT_ONLY=conf.PERMISSIONS_POLICY_REPORT_ONLY,
        ):
            response = self.client.get(reverse("login"))

        self.assertNotIn("Permissions-Policy-Report-Only", response)
        self.assertIn("geolocation=()", response["Permissions-Policy"])
