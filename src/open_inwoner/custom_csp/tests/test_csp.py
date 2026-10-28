import re

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from django_webtest import WebTest
from maykin_common.csp.constants import CSPDirective
from maykin_common.csp.models import CSPSetting

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.cms.tests import cms_tools

POLICY = (
    settings.CONTENT_SECURITY_POLICY or settings.CONTENT_SECURITY_POLICY_REPORT_ONLY
)

CSP_HEADER = "Content-Security-Policy"
CSP_RO_HEADER = "Content-Security-Policy-Report-Only"


PDOK_ACHTERGRONDKAART = (
    "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/"
)


def csp_headers(response) -> dict[str, dict[str, str]]:
    # the order of directives and sources doesn't matter and nonces are random per
    # request, so parse and normalize the policies to be able to compare them
    return {
        name: {
            directive: " ".join(sorted(sources))
            for directive, *sources in (
                directive.split()
                for directive in re.sub(r"'nonce-[^']+'", "'nonce'", value).split(";")
            )
        }
        for name, value in response.headers.items()
        if name in (CSP_HEADER, CSP_RO_HEADER)
    }


def sources(*values: str) -> str:
    # normalized like csp_headers, the Open Forms domain is empty unless configured
    return " ".join(sorted(source for value in values for source in value.split()))


class CSPSettingsTest(SimpleTestCase):
    def test_upgrade_insecure_requests_only_when_served_over_https(self):
        self.assertEqual(
            POLICY["DIRECTIVES"]["upgrade-insecure-requests"], settings.IS_HTTPS
        )


@override_settings(
    CONTENT_SECURITY_POLICY=POLICY,
    CONTENT_SECURITY_POLICY_REPORT_ONLY=None,
    # the cache is not reset between tests, nor invalidated by their rollback
    MKN_CSP_CACHE_TIMEOUT=0,
)
class CSPTest(WebTest):
    def setUp(self):
        super().setUp()
        # without any pages "/" is the django CMS welcome page, which doesn't use the
        # nonce, so django-csp leaves it out of the policy
        cms_tools.create_homepage()
        self.policy = csp_headers(self.app.get("/"))[CSP_HEADER]

    def test_csp_policy(self):
        response = self.app.get("/")

        self.assertEqual(
            csp_headers(response),
            {
                CSP_HEADER: {
                    "default-src": "'none'",
                    "base-uri": "'none'",
                    "font-src": sources("'self'", settings.OPEN_FORMS_SDK_DOMAIN),
                    "frame-ancestors": "'self'",
                    "frame-src": "'self'",
                    "object-src": "'none'",
                    "script-src": sources(
                        "'self'", "'nonce'", settings.OPEN_FORMS_SDK_DOMAIN
                    ),
                    "style-src": sources(
                        "'self'", "'nonce'", settings.OPEN_FORMS_SDK_DOMAIN
                    ),
                    # PDOK is added by the database
                    "img-src": sources(
                        "'self'",
                        "data:",
                        settings.OPEN_FORMS_SDK_DOMAIN,
                        PDOK_ACHTERGRONDKAART,
                    ),
                    "connect-src": sources("'self'", settings.OPEN_FORMS_API_DOMAIN),
                    "report-uri": reverse("report_csp"),
                }
            },
        )

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
                    "img-src": sources(self.policy["img-src"], "https://example.com"),
                }
            },
        )

    @override_settings(CONTENT_SECURITY_POLICY={**POLICY, "REPORT_PERCENTAGE": 0})
    def test_csp_report_uri_sampled_out_with_database_directives(self):
        CSPSetting.objects.create(
            directive=CSPDirective.IMG_SRC, value="https://example.com"
        )

        response = self.app.get("/")

        self.assertEqual(
            csp_headers(response),
            {
                CSP_HEADER: {
                    **{
                        directive: value
                        for directive, value in self.policy.items()
                        if directive != "report-uri"
                    },
                    "img-src": sources(self.policy["img-src"], "https://example.com"),
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
