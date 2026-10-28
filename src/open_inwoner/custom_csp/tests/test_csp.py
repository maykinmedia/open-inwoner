import re

from django.conf import settings
from django.test import override_settings

from django_webtest import WebTest
from maykin_common.csp.constants import CSPDirective
from maykin_common.csp.models import CSPSetting

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory

POLICY = (
    settings.CONTENT_SECURITY_POLICY or settings.CONTENT_SECURITY_POLICY_REPORT_ONLY
)

CSP_HEADER = "Content-Security-Policy"
CSP_RO_HEADER = "Content-Security-Policy-Report-Only"


def csp_headers(response) -> dict[str, dict[str, str]]:
    # directive order isn't stable and nonces are random per request, so parse and
    # normalize the policies to be able to compare them
    return {
        name: dict(
            directive.strip().partition(" ")[::2]
            for directive in re.sub(r"'nonce-[^']+'", "'nonce'", value).split(";")
        )
        for name, value in response.headers.items()
        if name in (CSP_HEADER, CSP_RO_HEADER)
    }


@override_settings(
    CONTENT_SECURITY_POLICY=POLICY,
    CONTENT_SECURITY_POLICY_REPORT_ONLY=None,
    # the cache is not reset between tests, nor invalidated by their rollback
    MKN_CSP_CACHE_TIMEOUT=0,
)
class CSPTest(WebTest):
    def setUp(self):
        super().setUp()
        self.policy = csp_headers(self.app.get("/"))[CSP_HEADER]

    def test_csp_enforced_for_anonymous(self):
        response = self.app.get("/")

        self.assertEqual(csp_headers(response), {CSP_HEADER: self.policy})

    def test_csp_enforced_for_digid_login(self):
        user = DigidUserFactory()
        response = self.app.get("/", user=user)

        self.assertEqual(csp_headers(response), {CSP_HEADER: self.policy})

    def test_csp_enforced_for_staff_login(self):
        user = UserFactory(is_staff=True)
        response = self.app.get("/", user=user)

        self.assertEqual(csp_headers(response), {CSP_HEADER: self.policy})

    def test_csp_includes_database_directives(self):
        CSPSetting.objects.create(
            directive=CSPDirective.IMG_SRC, value="https://example.com"
        )

        response = self.app.get("/")

        self.assertEqual(
            csp_headers(response),
            {
                CSP_HEADER: {
                    **self.policy,
                    "img-src": f"{self.policy['img-src']} https://example.com",
                }
            },
        )

    def test_csp_excluded_for_admin(self):
        user = UserFactory(is_staff=True)
        response = self.app.get("/admin/", user=user)

        self.assertEqual(csp_headers(response), {})

    def test_csp_excluded_for_anonymous_admin(self):
        response = self.app.get("/admin/login/")

        self.assertEqual(csp_headers(response), {})

    def test_csp_excluded_for_api_docs(self):
        response = self.app.get("/api/docs/")

        self.assertEqual(csp_headers(response), {})

    def test_csp_enforced_for_api(self):
        response = self.app.get("/api/products/", status="*")

        self.assertEqual(csp_headers(response), {CSP_HEADER: self.policy})

    @override_settings(
        CONTENT_SECURITY_POLICY=None,
        CONTENT_SECURITY_POLICY_REPORT_ONLY=POLICY,
    )
    def test_csp_report_only_mode(self):
        response = self.app.get("/")

        self.assertEqual(csp_headers(response), {CSP_RO_HEADER: self.policy})
