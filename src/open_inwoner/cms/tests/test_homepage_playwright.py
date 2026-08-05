from unittest.mock import MagicMock, patch

from django.test import override_settings, tag
from django.urls import reverse

from cms.api import add_plugin
from cms.models import PageContent, Placeholder
from playwright.sync_api import expect

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.cms.plugins.cms_plugins import CMSZakenPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.constants import TypeAanvraag
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import FormulierenResult, ZakenResult
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.utils.test import ClearCachesMixin
from open_inwoner.utils.tests.playwright import PlaywrightSyncLiveServerTestCase


@tag("e2e")
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class HomepagePlaywrightTests(ClearCachesMixin, PlaywrightSyncLiveServerTestCase):
    """
    Browser-level tests for plugins rendered on the homepage."""

    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory(bsn="900222086")
        self.user_login_state = self.get_user_bsn_login_state(self.user)

        self.homepage = cms_tools.create_homepage()

        # avoid the cookie banner overlapping/intercepting clicks on cards
        config = SiteConfiguration.get_solo()
        config.cookie_info_text = ""
        config.save()

    def _add_plugin_to_homepage(self, plugin_class, **plugin_data):
        """
        Add `plugin_class` to the homepage's `content` placeholder and
        (re)publish the page so it's visible to the live server.
        """
        page_content = PageContent._original_manager.get(
            page=self.homepage, language="nl"
        )
        placeholder = Placeholder.objects.get_for_obj(page_content).get(slot="content")
        add_plugin(
            placeholder=placeholder,
            plugin_type=plugin_class,
            language="nl",
            **plugin_data,
        )
        cms_tools.publish_page(self.homepage, "nl")

    def _mock_formulier_submission(
        self, *, vervolg_link, identification="SUBMISSION-001", naam="Test formulier"
    ):
        """
        Build a formulier submission mock as returned by `ZGWService.get_formulieren`.
        """
        api_group = ZGWApiGroupConfigFactory()

        mock_submission = MagicMock()
        mock_submission.process_data.return_value = {
            "uuid": "submission-uuid-1",
            "identification": identification,
            "naam": naam,
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.FORMULIER.value,
            "vervolg_link": vervolg_link,
        }
        return mock_submission

    def _mock_zaak(self, *, zaak_uuid, identification, naam):
        """
        Build a resolved zaak mock, as returned by `ZGWService.get_visible_zaken`
        and passed straight through the (patched) `fully_resolve_zaken`.

        Returns the mock together with its `ZGWApiGroupConfig`, so callers
        can build the expected detail URL from that concrete instance
        instead of reading it back off the mock.
        """
        api_group = ZGWApiGroupConfigFactory()

        mock_zaak = MagicMock()
        mock_zaak.process_data.return_value = {
            "uuid": zaak_uuid,
            "identification": identification,
            "naam": naam,
            "api_group": api_group,
            "type_aanvraag": TypeAanvraag.ZAAK.value,
        }
        return mock_zaak, api_group

    def _patch_zgw_service(self, *, formulieren, zaken=()):
        """
        Patch the `ZGWService` calls made by the zaken plugin's HTMX content
        view, so it returns `formulieren` and `zaken` without making any
        real ZGW API calls (`zaken` is passed through as-is, since
        `fully_resolve_zaken` is patched to a no-op).
        """
        return (
            patch(
                "open_inwoner.cms.plugins.views.ZGWService.get_formulieren",
                return_value=FormulierenResult(formulieren=formulieren),
            ),
            patch(
                "open_inwoner.cms.plugins.views.ZGWService.get_visible_zaken",
                return_value=ZakenResult(zaken=list(zaken), skipped=[]),
            ),
            patch(
                "open_inwoner.cms.plugins.views.ZGWService.fully_resolve_zaken",
                side_effect=lambda zaken: ZakenResult(zaken=zaken, skipped=[]),
            ),
        )

    # regression test for #2745
    def test_mijn_zaken_formulier_without_vervolg_link_renders_as_non_interactive_card(
        self,
    ):
        mock_submission = self._mock_formulier_submission(vervolg_link=None)
        self._add_plugin_to_homepage(CMSZakenPlugin, title="Mijn Zaken", num_zaken=4)

        patchers = self._patch_zgw_service(formulieren=[mock_submission])
        with patchers[0], patchers[1], patchers[2]:
            context = self.get_context(storage_state=self.user_login_state)
            page = context.new_page()
            page.goto(self.live_url("/"))

            card = page.locator("oip-home-plugin-card").first
            rendered_card = card.locator(".oip-home-plugin-card")
            expect(rendered_card).to_be_visible()
            expect(card.locator("a.oip-home-plugin-card")).to_have_count(0)

            url_before_click = page.url
            rendered_card.click()

            # a non-interactive card should never cause navigation
            expect(page).to_have_url(url_before_click)

    def test_mijn_zaken_formulier_with_vervolg_link_renders_as_link_to_vervolg_link(
        self,
    ):
        mock_submission = self._mock_formulier_submission(
            vervolg_link="https://example.com/formulier/123"
        )
        self._add_plugin_to_homepage(CMSZakenPlugin, title="Mijn Zaken", num_zaken=4)

        patchers = self._patch_zgw_service(formulieren=[mock_submission])
        with patchers[0], patchers[1], patchers[2]:
            context = self.get_context(storage_state=self.user_login_state)
            page = context.new_page()
            page.goto(self.live_url("/"))

            link = page.locator("oip-home-plugin-card a.oip-home-plugin-card").first
            expect(link).to_have_attribute("href", "https://example.com/formulier/123")

    def test_mijn_zaken_shows_each_formulier_and_zaak_with_own_title_label_and_link(
        self,
    ):
        formulier = self._mock_formulier_submission(
            identification="FORM-2025-001",
            naam="Kwijtschelding aanvraag",
            vervolg_link="https://example.com/formulier/456",
        )
        zaak_1, zaak_1_api_group = self._mock_zaak(
            zaak_uuid="zaak-uuid-1",
            identification="ZAAK-2025-042",
            naam="Vergunning aanvraag",
        )
        zaak_2, zaak_2_api_group = self._mock_zaak(
            zaak_uuid="zaak-uuid-2",
            identification="ZAAK-2025-043",
            naam="Melding openbare ruimte",
        )
        self._add_plugin_to_homepage(CMSZakenPlugin, title="Mijn Zaken", num_zaken=4)

        patchers = self._patch_zgw_service(
            formulieren=[formulier], zaken=[zaak_1, zaak_2]
        )
        with patchers[0], patchers[1], patchers[2]:
            context = self.get_context(storage_state=self.user_login_state)
            page = context.new_page()
            page.goto(self.live_url("/"))

            expect(page.locator("oip-home-plugin-card")).to_have_count(3)

            # the formulier has no case number, only a title and a real link
            formulier_card = page.locator(
                'oip-home-plugin-card[identificatie="FORM-2025-001"]'
            )
            expect(
                formulier_card.get_by_text("Kwijtschelding aanvraag")
            ).to_be_visible()
            expect(formulier_card.locator("a.oip-home-plugin-card")).to_have_attribute(
                "href", "https://example.com/formulier/456"
            )

            zaak_label = OpenZaakConfig.get_solo().zaak_identificatie_label
            for zaak_uuid, api_group, identification, naam in [
                (
                    "zaak-uuid-1",
                    zaak_1_api_group,
                    "ZAAK-2025-042",
                    "Vergunning aanvraag",
                ),
                (
                    "zaak-uuid-2",
                    zaak_2_api_group,
                    "ZAAK-2025-043",
                    "Melding openbare ruimte",
                ),
            ]:
                card = page.locator(
                    f'oip-home-plugin-card[identificatie="{identification}"]'
                )
                expect(card.get_by_text(naam)).to_be_visible()
                expect(
                    card.get_by_text(f"{zaak_label} {identification}")
                ).to_be_visible()

                expected_url = reverse(
                    "cases:case_detail",
                    kwargs={
                        "object_id": zaak_uuid,
                        "api_group_id": str(api_group.id),
                    },
                )
                expect(card.locator("a.oip-home-plugin-card")).to_have_attribute(
                    "href", expected_url
                )

    # -- Bfcache reload (BfcacheReloader) --------------------------------
    #
    # Real browser back/forward-cache restoration is too unreliable to force
    # deterministically in headless automation, so instead of navigating
    # away and back, these dispatch the same synthetic `pageshow` event a
    # real bfcache restore would - directly against the production bundle
    # running in a real browser, exercising the actual `BfcacheReloader`
    # wired up in `components/index.js`. What they don't cover is whether
    # Chromium actually chooses to bfcache this page; that's a browser
    # platform behaviour outside this code's control.

    def test_bfcache_restore_with_pending_load_element_triggers_reload(self):
        mock_submission = self._mock_formulier_submission(vervolg_link=None)
        self._add_plugin_to_homepage(CMSZakenPlugin, title="Mijn Zaken", num_zaken=4)

        patchers = self._patch_zgw_service(formulieren=[mock_submission])
        with patchers[0], patchers[1], patchers[2]:
            context = self.get_context(storage_state=self.user_login_state)
            page = context.new_page()
            page.goto(self.live_url("/"))
            page.wait_for_load_state("networkidle")

            # simulate a page that was frozen into bfcache before its
            # `hx-trigger="load"` request finished
            page.evaluate(
                """
                () => {
                  const stray = document.createElement('div');
                  stray.setAttribute('hx-trigger', 'load');
                  document.body.appendChild(stray);
                }
                """
            )
            page.evaluate("() => { window.__test_marker = true; }")

            with page.expect_navigation():
                page.evaluate(
                    "() => window.dispatchEvent("
                    "new PageTransitionEvent('pageshow', { persisted: true }))"
                )

            # a real navigation wipes the JS context, so the marker is gone
            self.assertIsNone(page.evaluate("() => window.__test_marker"))

    def test_bfcache_restore_without_pending_load_element_does_not_reload(self):
        mock_submission = self._mock_formulier_submission(vervolg_link=None)
        self._add_plugin_to_homepage(CMSZakenPlugin, title="Mijn Zaken", num_zaken=4)

        patchers = self._patch_zgw_service(formulieren=[mock_submission])
        with patchers[0], patchers[1], patchers[2]:
            context = self.get_context(storage_state=self.user_login_state)
            page = context.new_page()
            page.goto(self.live_url("/"))
            # zaken content has already loaded and swapped away the spinner,
            # so there's no pending `hx-trigger="load"` element left
            page.wait_for_load_state("networkidle")

            page.evaluate("() => { window.__test_marker = true; }")
            page.evaluate(
                "() => window.dispatchEvent("
                "new PageTransitionEvent('pageshow', { persisted: true }))"
            )
            page.wait_for_timeout(200)  # give a reload a moment, if one were coming

            self.assertTrue(page.evaluate("() => window.__test_marker"))
