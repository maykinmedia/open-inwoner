from django.test import TestCase
from django.urls import resolve, reverse

from open_inwoner.configurations.models import SiteConfiguration


class SecurityTxtRedirectTest(TestCase):
    def test_security_txt_url_registered_to_correct_path(self):
        self.assertEqual(reverse("security-txt-redirect"), "/.well-known/security.txt")

        resolve_match = resolve("/.well-known/security.txt")
        self.assertEqual(resolve_match.url_name, "security-txt-redirect")

    def test_security_txt_url_redirects_to_configured_url(self):
        config = SiteConfiguration.get_solo()
        config.security_txt_redirect_target = (
            "https://maykin.nl/.well-known/security.txt"
        )
        config.save()

        resp = self.client.get(
            path=reverse("security-txt-redirect"),
        )

        self.assertEqual(resp.status_code, 302, msg="Redirect is temporary")
        self.assertEqual(resp["Location"], "https://maykin.nl/.well-known/security.txt")

    def test_security_txt_url_redirect_disallows_non_safe_methods(self):
        url = reverse("security-txt-redirect")
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
            with self.subTest(method):
                do_request = getattr(self.client, method.lower())
                resp = do_request(url)

                self.assertEqual(resp.status_code, 405)
