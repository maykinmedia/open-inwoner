from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse, reverse_lazy

from open_inwoner.accounts.tests.factories import UserFactory

# Avoid redirects through `KvKLoginMiddleware`
PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]


@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls",
    MIDDLEWARE=PATCHED_MIDDLEWARE,
)
class OuterCaseListAccessTests(TestCase):
    outer_url = reverse_lazy("cases:index")

    def test_non_staff_user_without_bsn_or_kvk_is_denied(self):
        self.client.force_login(UserFactory(bsn="", kvk=""))

        response = self.client.get(self.outer_url)

        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(response, "pages/cases/list_outer.html")

    def test_staff_user_without_bsn_or_kvk_gets_outer_page(self):
        self.client.force_login(UserFactory(bsn="", kvk="", is_staff=True))

        response = self.client.get(self.outer_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/cases/list_outer.html")
        self.assertTemplateNotUsed(response, "pages/cases/403.html")

    def test_staff_user_without_bsn_or_kvk_is_denied_case_data(self):
        self.client.force_login(UserFactory(bsn="", kvk="", is_staff=True))

        response = self.client.get(
            reverse("cases:cases_content"), HTTP_HX_REQUEST="true"
        )

        self.assertTemplateUsed(response, "pages/cases/403.html")
        self.assertTemplateNotUsed(response, "pages/cases/list_inner.html")
