import re

from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.media.tests.factories import VideoFactory
from open_inwoner.pdc.tests.factories import ProductFactory, ProductLocationFactory

from .test_csp import CSP_HEADER, POLICY

# browsers don't execute these, so they don't need a nonce
DATA_SCRIPT_TYPES = ("application/json", "application/ld+json")


def blocked_by_csp(response) -> list[str]:
    """
    Describe the inline scripts, styles and attributes the policy would block.

    Scripts and styles from our own origin are allowed by 'self', but anything
    inline needs the nonce of the response, and inline event handlers and style
    attributes are not allowed at all.
    """
    nonce = re.search(r"'nonce-([^']+)'", response.headers[CSP_HEADER]).group(1)
    blocked = []

    for element in response.pyquery("script:not([src]), style"):
        if element.tag == "script" and element.get("type") in DATA_SCRIPT_TYPES:
            continue
        if element.get("nonce") != nonce:
            blocked.append(f"<{element.tag}> without nonce")

    blocked.extend(
        f"<{element.tag} {attribute}=...>"
        for element in response.pyquery("*")
        for attribute in element.attrib
        if attribute == "style" or attribute.startswith("on")
    )

    return blocked


@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls",
    CONTENT_SECURITY_POLICY=POLICY,
    CONTENT_SECURITY_POLICY_REPORT_ONLY=None,
)
class TemplatesCSPTest(WebTest):
    def setUp(self):
        super().setUp()
        cms_tools.create_homepage()

    def test_homepage(self):
        response = self.app.get("/")

        self.assertEqual(blocked_by_csp(response), [])

    def test_product_with_map_and_video(self):
        product = ProductFactory(video=VideoFactory())
        product.locations.add(ProductLocationFactory())

        response = self.app.get(
            reverse("products:product_detail", kwargs={"slug": product.slug})
        )

        # make sure the parts with external sources are actually rendered
        self.assertEqual(len(response.pyquery(".map__leaflet")), 1)
        self.assertEqual(len(response.pyquery(".video iframe")), 1)
        self.assertEqual(blocked_by_csp(response), [])

    def test_profile(self):
        ProfileConfig.objects.create(namespace=ProfileApphook.app_name)
        cms_tools.create_apphook_page(ProfileApphook)

        response = self.app.get(reverse("profile:detail"), user=DigidUserFactory())

        self.assertEqual(blocked_by_csp(response), [])
