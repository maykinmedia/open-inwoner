from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse, reverse_lazy

from pyquery import PyQuery

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.cases.views.cases import InnerCaseListView
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import (
    FormulierenResult,
    SkippedZaak,
    SkipReason,
    ZakenResult,
)
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.utils.test import ClearCachesMixin

# Avoid redirects through `KvKLoginMiddleware`
PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]

_VIEW_MODULE = "open_inwoner.cms.cases.views.cases"


@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls",
    MIDDLEWARE=PATCHED_MIDDLEWARE,
)
class CaseListPartialResultsTests(ClearCachesMixin, TestCase):
    """
    When the case list is incomplete because a fetch stage timed out, the user
    must be told and the view must retry a bounded number of times.

    Regression tests for #2735: zaken silently disappeared from the first render
    and only showed up after the user clicked "Mijn zaken" a second time.
    """

    inner_url = reverse_lazy("cases:cases_content")

    def setUp(self):
        super().setUp()

        self.user = UserFactory(
            login_type=LoginTypeChoices.digid, bsn="900222086", email="john@smith.nl"
        )
        self.api_group = ZGWApiGroupConfigFactory()
        self.client.force_login(self.user)

    def _patch_service(
        self,
        *,
        visible_result: ZakenResult | None = None,
        formulieren_result: FormulierenResult | None = None,
        resolved_result: ZakenResult | None = None,
        search_result: ZakenResult | None = None,
    ):
        """Patch the whole service so no HTTP or DB fixtures are needed."""
        service = patch(f"{_VIEW_MODULE}.ZGWService").start()
        self.addCleanup(patch.stopall)

        instance = service.return_value
        instance.get_visible_zaken.return_value = visible_result or ZakenResult(
            zaken=[], skipped=[]
        )
        instance.get_formulieren.return_value = formulieren_result or FormulierenResult(
            formulieren=[]
        )
        instance.fully_resolve_zaken.return_value = resolved_result or ZakenResult(
            zaken=[], skipped=[]
        )
        instance.search_zaken.return_value = search_result or ZakenResult(
            zaken=[], skipped=[]
        )
        return instance

    def _timeout_skip(self) -> SkippedZaak:
        return SkippedZaak(
            zaak_url="http://zaken.nl/api/v1/zaken/1234",
            reason=SkipReason.TIMEOUT,
            api_group=self.api_group,
        )

    def _get(self, **params):
        response = self.client.get(self.inner_url, params, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        return PyQuery(response.content)

    def _retry_element(self, doc):
        return doc.find(".cases__auto-retry")

    def _notifications(self, doc):
        return doc.find(".notification--warning")

    def test_no_banner_and_no_retry_when_results_are_complete(self):
        self._patch_service()

        doc = self._get()

        self.assertEqual(len(self._notifications(doc)), 0)
        self.assertEqual(len(self._retry_element(doc)), 0)

    def test_no_banner_for_non_timeout_skips(self):
        """Zaken excluded on confidentiality grounds are not a partial result."""
        self._patch_service(
            visible_result=ZakenResult(
                zaken=[],
                skipped=[
                    SkippedZaak(
                        zaak_url="http://zaken.nl/api/v1/zaken/1234",
                        reason=SkipReason.CONFIDENTIALITY_TOO_HIGH,
                        api_group=self.api_group,
                    )
                ],
            )
        )

        doc = self._get()

        self.assertEqual(len(self._notifications(doc)), 0)
        self.assertEqual(len(self._retry_element(doc)), 0)

    def test_banner_and_retry_on_raw_fetch_timeout(self):
        self._patch_service(
            visible_result=ZakenResult(zaken=[], skipped=[], raw_fetch_incomplete=True)
        )

        doc = self._get()

        self.assertEqual(len(self._notifications(doc)), 1)

        retry = self._retry_element(doc)
        self.assertEqual(len(retry), 1)
        self.assertEqual(retry.attr("hx-target"), "#cases-content")
        self.assertEqual(
            retry.attr("hx-trigger"),
            f"load delay:{InnerCaseListView.AUTO_RETRY_DELAY_S}s",
        )
        self.assertIn("retry=1", retry.attr("hx-get"))

    def test_banner_and_retry_on_zaaktype_stage_timeout(self):
        self._patch_service(
            visible_result=ZakenResult(zaken=[], skipped=[self._timeout_skip()])
        )

        doc = self._get()

        self.assertEqual(len(self._notifications(doc)), 1)
        self.assertEqual(len(self._retry_element(doc)), 1)

    def test_banner_and_retry_on_formulieren_timeout(self):
        self._patch_service(
            formulieren_result=FormulierenResult(formulieren=[], timed_out=True)
        )

        doc = self._get()

        self.assertEqual(len(self._notifications(doc)), 1)
        self.assertEqual(len(self._retry_element(doc)), 1)

    def test_banner_and_retry_on_full_resolution_timeout(self):
        self._patch_service(
            resolved_result=ZakenResult(zaken=[], skipped=[self._timeout_skip()])
        )

        doc = self._get()

        self.assertEqual(len(self._notifications(doc)), 1)
        self.assertEqual(len(self._retry_element(doc)), 1)

    def test_banner_and_retry_on_search_timeout(self):
        self._patch_service(
            search_result=ZakenResult(zaken=[], skipped=[], raw_fetch_incomplete=True)
        )

        doc = self._get(search="ZAAK-2022-0000000024")

        self.assertEqual(len(self._notifications(doc)), 1)

        retry = self._retry_element(doc)
        self.assertEqual(len(retry), 1)
        self.assertIn("search=ZAAK-2022-0000000024", retry.attr("hx-get"))

    def test_retry_counter_increments(self):
        self._patch_service(
            visible_result=ZakenResult(zaken=[], skipped=[], raw_fetch_incomplete=True)
        )

        doc = self._get(retry=1)

        retry = self._retry_element(doc)
        self.assertEqual(len(retry), 1)
        self.assertIn("retry=2", retry.attr("hx-get"))

    def test_exhausted_retries_show_manual_retry_link(self):
        self._patch_service(
            visible_result=ZakenResult(zaken=[], skipped=[], raw_fetch_incomplete=True)
        )

        doc = self._get(retry=InnerCaseListView.MAX_AUTO_RETRIES)

        self.assertEqual(len(self._notifications(doc)), 1)
        self.assertEqual(len(self._retry_element(doc)), 0)

        # the link points at the outer page, which starts a fresh retry cycle
        href = self._notifications(doc).find("a").attr("href")
        self.assertEqual(href, reverse("cases:index"))

    def test_manual_retry_link_preserves_filters_and_drops_retry_param(self):
        self._patch_service(
            search_result=ZakenResult(zaken=[], skipped=[], raw_fetch_incomplete=True)
        )

        doc = self._get(
            retry=InnerCaseListView.MAX_AUTO_RETRIES,
            search="ZAAK-2022-0000000024",
        )

        href = self._notifications(doc).find("a").attr("href")
        self.assertIn("search=ZAAK-2022-0000000024", href)
        self.assertNotIn("retry=", href)

    def test_auto_retry_url_preserves_multi_valued_status_filter(self):
        # The dummy zaken below cannot survive status filtering, so make the
        # assumption explicit that the filter (and hence the frequency counting
        # over the zaken) stays disabled: this test is about URL parameters only.
        config = OpenZaakConfig.get_solo()
        config.zaken_filter_enabled = False
        config.save()

        # enough zaken for page 2 to exist, so the retry survives pagination
        self._patch_service(
            visible_result=ZakenResult(
                zaken=[object() for _ in range(12)],
                skipped=[],
                raw_fetch_incomplete=True,
            )
        )

        response = self.client.get(
            self.inner_url,
            {
                "status": ["Lopende aanvragen", "Afgeronde aanvragen"],
                "page": 2,
            },
            HTTP_HX_REQUEST="true",
        )
        doc = PyQuery(response.content)

        hx_get = self._retry_element(doc).attr("hx-get")
        self.assertIn("status=Lopende+aanvragen", hx_get)
        self.assertIn("status=Afgeronde+aanvragen", hx_get)
        self.assertIn("page=2", hx_get)
        self.assertIn("retry=1", hx_get)

    def test_garbage_retry_param_is_treated_as_first_attempt(self):
        self._patch_service(
            visible_result=ZakenResult(zaken=[], skipped=[], raw_fetch_incomplete=True)
        )

        doc = self._get(retry="not-a-number")

        self.assertIn("retry=1", self._retry_element(doc).attr("hx-get"))

    def test_out_of_range_retry_param_is_clamped_to_maximum(self):
        self._patch_service(
            visible_result=ZakenResult(zaken=[], skipped=[], raw_fetch_incomplete=True)
        )

        doc = self._get(retry=99)

        # clamped to MAX_AUTO_RETRIES, so no further auto-retry is offered
        self.assertEqual(len(self._retry_element(doc)), 0)
        self.assertEqual(len(self._notifications(doc)), 1)

    def test_negative_retry_param_is_treated_as_first_attempt(self):
        self._patch_service(
            visible_result=ZakenResult(zaken=[], skipped=[], raw_fetch_incomplete=True)
        )

        doc = self._get(retry=-5)

        self.assertIn("retry=1", self._retry_element(doc).attr("hx-get"))

    def test_fetch_error_page_has_no_banner_or_retry(self):
        instance = self._patch_service()
        instance.get_visible_zaken.side_effect = RuntimeError("API error")

        doc = self._get()

        self.assertEqual(len(self._notifications(doc)), 0)
        self.assertEqual(len(self._retry_element(doc)), 0)
        self.assertIn("Er is iets misgegaan bij het ophalen van uw zaken", doc.text())
