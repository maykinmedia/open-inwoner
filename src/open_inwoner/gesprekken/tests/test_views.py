import re
import uuid
from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock
from zgw_consumers.constants import AuthTypes

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.gesprekken.models import GesprekGezien, MijnGesprekkenConfig
from open_inwoner.gesprekken.services import (
    BESTAND_POGINGEN,
    bump_versie,
    get_versie,
)
from open_inwoner.openklant.tests.factories import OpenKlant2ConfigFactory
from open_inwoner.openzaak.tests.factories import (
    ServiceFactory,
    ZGWApiGroupConfigFactory,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from .shared import (
    BESTAND_URL,
    DOWNLOAD_URL,
    FILE_ID,
    GESPREK_URL,
    GESPREK_UUID,
    GESPREKKEN_ROOT,
    PARTIJ,
    PARTIJ_DEELNAME,
    PARTIJ_UUID,
    UPLOAD_URL,
    ZAAK_URL,
    bestand,
    gesprek_detail,
)

ZAAK_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ACTOR = "https://klantinteracties.example.nl/api/v1/actoren/gemeente"


class GesprekkenViewTestBase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()
        site = SiteConfiguration.get_solo()
        site.name = "Gemeente Voorbeeld"
        site.save()

        self.config = MijnGesprekkenConfig.get_solo()
        self.config.enabled = True
        self.config.service = ServiceFactory(
            api_root=GESPREKKEN_ROOT,
            auth_type=AuthTypes.api_key,
            header_key="Authorization",
            header_value="Token geheim",
        )
        self.config.bijlagen_ingeschakeld = True
        self.config.save()

        self.user = DigidUserFactory(bsn="100000001")
        self.client.force_login(self.user)
        self.api_group = ZGWApiGroupConfigFactory()

        self.zaak = MagicMock(
            url=ZAAK_URL,
            uuid=uuid.UUID(ZAAK_UUID),
            einddatum=None,
        )
        access = patch(
            "open_inwoner.cms.cases.views.mixins.ZGWService.check_zaak_access",
            side_effect=lambda *args: (self.zaak, self.api_group),
        )
        access.start()
        self.addCleanup(access.stop)

        self.url = reverse(
            "cases:case_detail_gesprekken",
            kwargs={"api_group_id": self.api_group.id, "object_id": ZAAK_UUID},
        )

    def mock_api(self, m, detail=None):
        detail = detail or gesprek_detail()
        m.get(
            f"{GESPREKKEN_ROOT}gesprekken?aanleidingZaak={ZAAK_URL}",
            json=paginated_response([detail]),
        )
        m.get(f"{GESPREKKEN_ROOT}gesprekken/{GESPREK_UUID}", json=detail)
        m.post(requests_mock.ANY, status_code=201, json={})

    def mock_upload(self, m, *statussen):
        """An upload-sessie and a bestand that goes through these statussen."""
        m.post(
            f"{GESPREKKEN_ROOT}bestanden/upload-sessie",
            status_code=201,
            json={
                "fileId": FILE_ID,
                "uploadUrl": UPLOAD_URL,
                "verlooptOp": "2026-07-13T07:45:00Z",
                "bestand": bestand("uploadInAfwachting"),
            },
        )
        self.opslag_inhoud = []

        def opslag(request, context):
            self.opslag_inhoud.append(request.body.read())
            return ""

        m.put(UPLOAD_URL, text=opslag)
        m.get(BESTAND_URL, [{"json": bestand(status)} for status in statussen])


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@requests_mock.Mocker()
class GesprekkenSectionTests(GesprekkenViewTestBase):
    def test_shows_own_bijdragen_as_u_and_staff_as_the_organisation(self, m):
        self.mock_api(m)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Onderwerp van het gesprek", content)
        self.assertIn("Gestart op: 12/06/2026", content)
        self.assertIn('<span class="gesprekken__afzender">U</span>', content)
        self.assertNotIn("ontwerp volgt", content)
        self.assertIn("Gemeente Voorbeeld", content)
        self.assertNotIn("M. Medewerker", content)
        self.assertIn("13/07/2026", content)
        self.assertIn('name="bijlage"', content)

    def test_seeing_a_gesprek_registers_gelezen_for_bijdragen_of_others(self, m):
        self.mock_api(m)

        self.client.get(self.url)

        gelezen = [
            r
            for r in m.request_history
            if r.method == "POST" and r.url.endswith("/gelezen")
        ]
        self.assertEqual(len(gelezen), 1)
        self.assertIn("55555555-5555-5555-5555-555555555555", gelezen[0].url)
        self.assertEqual(gelezen[0].json(), {"gespreksdeelname": PARTIJ_DEELNAME})
        self.assertTrue(GesprekGezien.objects.filter(user=self.user).exists())

    def test_polling_gets_204_while_nothing_changed(self, m):
        self.mock_api(m)
        versie = bump_versie(ZAAK_URL)

        response = self.client.get(self.url, {"versie": versie})

        self.assertEqual(response.status_code, 204)
        self.assertEqual(m.call_count, 0)

    def test_polling_gets_the_section_after_a_change(self, m):
        self.mock_api(m)
        oud = bump_versie(ZAAK_URL)
        bump_versie(ZAAK_URL)

        response = self.client.get(self.url, {"versie": oud})

        self.assertEqual(response.status_code, 200)

    def test_polling_trigger_needs_no_htmx_eval(self, m):
        # OIP sets htmx.config.allowEval = false, so a [filter] in hx-trigger
        # raises htmx:evalDisallowedError (and the generic error banner).
        self.mock_api(m)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        trigger = re.search(r'hx-trigger="([^"]*)"', response.content.decode())
        self.assertIsNotNone(trigger)
        self.assertNotIn("[", trigger[1])

    def test_a_closed_zaak_shows_the_message_and_no_input(self, m):
        self.mock_api(m)
        self.zaak.einddatum = "2026-06-28"

        content = self.client.get(self.url).content.decode()

        self.assertIn("Zaak is gesloten", content)
        self.assertNotIn("<textarea", content)

    def test_closed_gesprekken_are_on_the_gesloten_tab(self, m):
        self.mock_api(m, gesprek_detail(beeindigd=True))

        open_tab = self.client.get(self.url).content.decode()
        gesloten_tab = self.client.get(self.url, {"tab": "gesloten"}).content.decode()

        self.assertIn("geen open gesprekken", open_tab)
        self.assertIn("Onderwerp van het gesprek", gesloten_tab)
        self.assertNotIn("<textarea", gesloten_tab)

    def test_no_start_button_by_default(self, m):
        self.mock_api(m, gesprek_detail(bijdragen=[]))

        content = self.client.get(self.url).content.decode()

        self.assertNotIn("Nieuw gesprek", content)

    def test_disabled_section_is_not_found(self, m):
        MijnGesprekkenConfig.objects.update(enabled=False)

        self.assertEqual(self.client.get(self.url).status_code, 404)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@requests_mock.Mocker()
class GesprekBijdrageTests(GesprekkenViewTestBase):
    def bijdrage_url(self):
        return reverse(
            "cases:case_detail_gesprek_bijdrage",
            kwargs={
                "api_group_id": self.api_group.id,
                "object_id": ZAAK_UUID,
                "gesprek_uuid": GESPREK_UUID,
            },
        )

    def posted_bijdragen(self, m):
        return [
            r.json()
            for r in m.request_history
            if r.method == "POST" and r.url.endswith("/gespreksbijdragen")
        ]

    def test_a_bijdrage_is_sent_as_the_own_deelname_and_the_page_is_marked_changed(
        self, m
    ):
        self.mock_api(m)
        voor = get_versie(ZAAK_URL)

        response = self.client.post(
            self.bijdrage_url(), {"tekst": "Hier is mijn antwoord"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.posted_bijdragen(m),
            [
                {
                    "gesprek": GESPREK_URL,
                    "tekstGespreksBijdrage": "Hier is mijn antwoord",
                    "bijlagen": [],
                    "verzender": {"gespreksdeelname": PARTIJ_DEELNAME},
                }
            ],
        )
        self.assertNotEqual(get_versie(ZAAK_URL), voor)

    def post_met_bijlage(self):
        return self.client.post(
            self.bijdrage_url(),
            {
                "tekst": "Zie bijlage",
                "bijlage": SimpleUploadedFile(
                    "loonstrook.pdf", b"%PDF", content_type="application/pdf"
                ),
            },
        )

    def test_a_bijlage_goes_through_an_upload_sessie_and_is_referenced_by_url(self, m):
        self.mock_api(m)
        self.mock_upload(m, "beschikbaar")

        self.post_met_bijlage()

        sessie = next(r for r in m.request_history if r.path.endswith("/upload-sessie"))
        self.assertEqual(
            sessie.json(),
            {
                "bestandsnaam": "loonstrook.pdf",
                "bestandsomvang": 4,
                "contentType": "application/pdf",
            },
        )
        self.assertEqual(self.opslag_inhoud, [b"%PDF"])
        self.assertEqual(
            self.posted_bijdragen(m)[0]["bijlagen"], [{"bestand": BESTAND_URL}]
        )

    def test_the_put_to_the_storage_carries_no_api_credentials(self, m):
        self.mock_api(m)
        self.mock_upload(m, "beschikbaar")

        self.post_met_bijlage()

        sessie = next(r for r in m.request_history if r.path.endswith("/upload-sessie"))
        put = next(r for r in m.request_history if r.method == "PUT")
        self.assertEqual(sessie.headers["Authorization"], "Token geheim")
        self.assertNotIn("Authorization", put.headers)
        self.assertEqual(put.headers["Content-Type"], "application/pdf")

    @patch("open_inwoner.gesprekken.services.time.sleep")
    def test_the_bijdrage_waits_until_the_bestand_is_beschikbaar(self, m, sleep):
        self.mock_api(m)
        self.mock_upload(m, "uploadInAfwachting", "uploadInAfwachting", "beschikbaar")

        self.post_met_bijlage()

        self.assertEqual(sleep.call_count, 2)
        self.assertEqual(len(self.posted_bijdragen(m)), 1)

    @patch("open_inwoner.gesprekken.services.time.sleep")
    def test_waiting_for_the_bestand_is_bounded(self, m, sleep):
        self.mock_api(m)
        self.mock_upload(m, "uploadInAfwachting")

        response = self.post_met_bijlage()

        statusvragen = [r for r in m.request_history if r.url == BESTAND_URL]
        self.assertEqual(len(statusvragen), BESTAND_POGINGEN)
        self.assertEqual(self.posted_bijdragen(m), [])
        self.assertIn("uploaden van de bijlage is mislukt", response.content.decode())

    def test_a_geweigerd_bestand_is_an_error_for_the_user(self, m):
        self.mock_api(m)
        self.mock_upload(m, "geweigerd")

        response = self.post_met_bijlage()

        self.assertEqual(self.posted_bijdragen(m), [])
        content = response.content.decode()
        self.assertIn("De bijlage is geweigerd", content)
        # The message of the user is not lost
        self.assertIn(">Zie bijlage</textarea>", content)

    def test_a_verlopen_bestand_is_not_retried(self, m):
        self.mock_api(m)
        self.mock_upload(m, "verlopen")

        response = self.post_met_bijlage()

        self.assertEqual(self.posted_bijdragen(m), [])
        self.assertIn("uploaden van de bijlage is mislukt", response.content.decode())

    def test_a_refused_put_stops_the_bijdrage(self, m):
        self.mock_api(m)
        self.mock_upload(m, "beschikbaar")
        m.put(UPLOAD_URL, status_code=403)

        response = self.post_met_bijlage()

        self.assertEqual(self.posted_bijdragen(m), [])
        self.assertIn("uploaden van de bijlage is mislukt", response.content.decode())

    def test_a_too_large_bestand_says_so(self, m):
        self.mock_api(m)
        m.post(f"{GESPREKKEN_ROOT}bestanden/upload-sessie", status_code=413)

        response = self.post_met_bijlage()

        self.assertEqual(self.posted_bijdragen(m), [])
        self.assertIn("De bijlage is te groot", response.content.decode())

    def test_no_upload_when_bijlagen_are_disabled(self, m):
        MijnGesprekkenConfig.objects.update(bijlagen_ingeschakeld=False)
        self.mock_api(m)

        response = self.post_met_bijlage()

        self.assertFalse(
            any(r.path.endswith("/upload-sessie") for r in m.request_history)
        )
        self.assertEqual(self.posted_bijdragen(m), [])
        self.assertIn("Bijlagen zijn niet ingeschakeld", response.content.decode())

    def test_no_bijdrage_to_a_closed_gesprek(self, m):
        self.mock_api(m, gesprek_detail(beeindigd=True))

        response = self.client.post(self.bijdrage_url(), {"tekst": "Nog iets"})

        self.assertEqual(self.posted_bijdragen(m), [])
        self.assertIn("Dit gesprek is gesloten", response.content.decode())

    def test_no_bijdrage_on_a_closed_zaak(self, m):
        self.mock_api(m)
        self.zaak.einddatum = "2026-06-28"

        self.client.post(self.bijdrage_url(), {"tekst": "Nog iets"})

        self.assertEqual(self.posted_bijdragen(m), [])

    def test_a_gesprek_of_another_zaak_is_not_found(self, m):
        detail = gesprek_detail()
        detail["aanleidingZaak"] = "https://zaken.nl/api/v1/zaken/andere-zaak"
        self.mock_api(m, detail)

        response = self.client.post(self.bijdrage_url(), {"tekst": "Hallo"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.posted_bijdragen(m), [])


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@requests_mock.Mocker()
class GesprekStartTests(GesprekkenViewTestBase):
    def setUp(self):
        super().setUp()
        self.user.first_name = "Piet"
        self.user.infix = ""
        self.user.last_name = "Jansen"
        self.user.save()
        self.config.burger_mag_gesprek_starten = True
        self.config.ontvanger_actor_url = ACTOR
        self.config.ontvanger_actor_naam = "Team Vergunningen"
        self.config.save()

        OpenKlant2ConfigFactory(
            service__api_root="https://klantinteracties.example.nl/api/v1/"
        )
        self.partij = patch(
            "open_inwoner.openklant.services.OpenKlant2Service.get_partij_for_user",
            return_value={"uuid": PARTIJ_UUID},
        )
        self.partij_lookup = self.partij.start()
        self.addCleanup(self.partij.stop)

        self.start_url = reverse(
            "cases:case_detail_gesprek_start",
            kwargs={"api_group_id": self.api_group.id, "object_id": ZAAK_UUID},
        )

    def mock_start(self, m, **kwargs):
        self.mock_api(m)
        return m.post(
            f"{GESPREKKEN_ROOT}gesprekken",
            **(kwargs or {"status_code": 201, "json": gesprek_detail()}),
        )

    def assert_no_start_form(self):
        content = self.client.get(self.url).content.decode()
        self.assertNotIn("Nieuw gesprek", content)

    def test_the_form_is_shown_on_an_open_zaak(self, m):
        self.mock_api(m)

        content = self.client.get(self.url).content.decode()

        self.assertIn("Nieuw gesprek", content)
        self.assertIn('name="onderwerp"', content)

    def test_no_form_without_permission_for_residents(self, m):
        self.mock_api(m)
        MijnGesprekkenConfig.objects.update(burger_mag_gesprek_starten=False)

        self.assert_no_start_form()

    def test_no_form_without_an_ontvanger(self, m):
        self.mock_api(m)
        MijnGesprekkenConfig.objects.update(ontvanger_actor_url="")

        self.assert_no_start_form()

    def test_no_form_without_a_partij(self, m):
        self.mock_api(m)
        self.partij_lookup.return_value = None

        self.assert_no_start_form()

    def test_no_form_on_a_closed_zaak(self, m):
        self.mock_api(m)
        self.zaak.einddatum = "2026-06-28"

        self.assert_no_start_form()

    def test_a_gesprek_is_started_with_the_partij_and_the_actor(self, m):
        start = self.mock_start(m)
        voor = get_versie(ZAAK_URL)

        response = self.client.post(
            self.start_url, {"onderwerp": "Mijn vraag", "tekst": "Hoe zit het?"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            start.last_request.json(),
            {
                "gespreksonderwerp": "Mijn vraag",
                "aanleidingZaak": ZAAK_URL,
                "ontvanger": [
                    {"type": "actor", "actor": ACTOR, "naam": "Team Vergunningen"}
                ],
                "eersteBijdrage": {
                    "tekstGespreksBijdrage": "Hoe zit het?",
                    "bijlagen": [],
                    "verzender": {
                        "nieuweDeelname": {
                            "type": "partij",
                            "partij": PARTIJ,
                            "naam": "Piet Jansen",
                        }
                    },
                },
            },
        )
        self.assertNotEqual(get_versie(ZAAK_URL), voor)
        # The section opens on the new gesprek
        self.assertIn('aria-expanded="true"', response.content.decode())

    def test_a_gesprek_can_start_with_a_bijlage(self, m):
        start = self.mock_start(m)
        self.mock_upload(m, "beschikbaar")

        self.client.post(
            self.start_url,
            {
                "onderwerp": "Mijn vraag",
                "tekst": "Zie bijlage",
                "bijlage": SimpleUploadedFile("loonstrook.pdf", b"%PDF"),
            },
        )

        self.assertEqual(
            start.last_request.json()["eersteBijdrage"]["bijlagen"],
            [{"bestand": BESTAND_URL}],
        )

    def test_a_refused_bijlage_starts_no_gesprek_and_keeps_the_input(self, m):
        start = self.mock_start(m)
        self.mock_upload(m, "geweigerd")

        response = self.client.post(
            self.start_url,
            {
                "onderwerp": "Mijn vraag",
                "tekst": "Zie bijlage",
                "bijlage": SimpleUploadedFile("virus.exe", b"MZ"),
            },
        )

        self.assertFalse(start.called)
        content = response.content.decode()
        self.assertIn("De bijlage is geweigerd", content)
        self.assertIn('value="Mijn vraag"', content)
        self.assertIn('class="gesprekken__start" open', content)

    def test_an_api_error_is_shown(self, m):
        self.mock_start(m, status_code=500)

        response = self.client.post(
            self.start_url, {"onderwerp": "Mijn vraag", "tekst": "Hoe zit het?"}
        )

        self.assertIn("Het starten is mislukt", response.content.decode())

    def test_an_incomplete_form_starts_nothing(self, m):
        start = self.mock_start(m)

        response = self.client.post(self.start_url, {"onderwerp": "Mijn vraag"})

        self.assertFalse(start.called)
        self.assertIn("Controleer uw bericht", response.content.decode())

    def test_posting_is_refused_without_a_partij(self, m):
        start = self.mock_start(m)
        self.partij_lookup.return_value = None

        response = self.client.post(
            self.start_url, {"onderwerp": "Mijn vraag", "tekst": "Hoe zit het?"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(start.called)

    def test_posting_is_refused_without_an_ontvanger(self, m):
        start = self.mock_start(m)
        MijnGesprekkenConfig.objects.update(ontvanger_actor_naam="")

        response = self.client.post(
            self.start_url, {"onderwerp": "Mijn vraag", "tekst": "Hoe zit het?"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(start.called)

    def test_posting_is_refused_on_a_closed_zaak(self, m):
        start = self.mock_start(m)
        self.zaak.einddatum = "2026-06-28"

        response = self.client.post(
            self.start_url, {"onderwerp": "Mijn vraag", "tekst": "Hoe zit het?"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(start.called)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@requests_mock.Mocker()
class GesprekEindigenTests(GesprekkenViewTestBase):
    def setUp(self):
        super().setUp()
        self.eindigen_url = reverse(
            "cases:case_detail_gesprek_eindigen",
            kwargs={
                "api_group_id": self.api_group.id,
                "object_id": ZAAK_UUID,
                "gesprek_uuid": GESPREK_UUID,
            },
        )

    def mock_eindigen(self, m, detail=None, **kwargs):
        self.mock_api(m, detail)
        return m.post(
            f"{GESPREKKEN_ROOT}gesprekken/{GESPREK_UUID}/eindigen",
            **(kwargs or {"json": gesprek_detail(beeindigd=True)}),
        )

    def test_an_open_gesprek_has_a_close_button(self, m):
        self.mock_api(m)

        content = self.client.get(self.url).content.decode()

        self.assertIn(f'hx-post="{self.eindigen_url}"', content)
        self.assertIn("Vraag beantwoord", content)

    def test_a_closed_gesprek_has_no_close_button(self, m):
        self.mock_api(m, gesprek_detail(beeindigd=True))

        content = self.client.get(self.url, {"tab": "gesloten"}).content.decode()

        self.assertNotIn("Vraag beantwoord", content)

    def test_the_resident_closes_the_gesprek(self, m):
        eindigen = self.mock_eindigen(m)
        voor = get_versie(ZAAK_URL)

        response = self.client.post(self.eindigen_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(eindigen.call_count, 1)
        self.assertIsNone(eindigen.last_request.body)
        self.assertNotEqual(get_versie(ZAAK_URL), voor)

    def test_a_gesprek_of_another_zaak_is_not_found(self, m):
        detail = gesprek_detail()
        detail["aanleidingZaak"] = "https://zaken.nl/api/v1/zaken/andere-zaak"
        eindigen = self.mock_eindigen(m, detail)

        response = self.client.post(self.eindigen_url)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(eindigen.called)

    def test_without_an_active_deelname_nothing_is_closed(self, m):
        detail = gesprek_detail()
        detail["gespreksdeelnames"][0]["momentEindeDeelname"] = "2026-07-01T09:00:00Z"
        eindigen = self.mock_eindigen(m, detail)

        response = self.client.post(self.eindigen_url)

        self.assertFalse(eindigen.called)
        self.assertIn("U neemt niet deel", response.content.decode())

    def test_a_closed_gesprek_is_not_closed_again(self, m):
        eindigen = self.mock_eindigen(m, gesprek_detail(beeindigd=True))

        response = self.client.post(self.eindigen_url)

        self.assertFalse(eindigen.called)
        self.assertIn("Dit gesprek is gesloten", response.content.decode())

    def test_an_api_error_is_shown(self, m):
        self.mock_eindigen(m, status_code=403)

        response = self.client.post(self.eindigen_url)

        self.assertIn("Het afsluiten is mislukt", response.content.decode())


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@requests_mock.Mocker()
class GesprekBijlageDownloadTests(GesprekkenViewTestBase):
    def setUp(self):
        super().setUp()
        self.detail = gesprek_detail()
        self.detail["gespreksbijdragen"][0]["bijlagen"] = [
            {
                "bestand": BESTAND_URL,
                "bestandsnaam": "loonstrook.pdf",
                "contentType": "application/pdf",
                "bestandsomvang": 184320,
            }
        ]

    def bijlage_url(self, file_id=FILE_ID):
        return reverse(
            "cases:case_detail_gesprek_bijlage",
            kwargs={
                "api_group_id": self.api_group.id,
                "object_id": ZAAK_UUID,
                "gesprek_uuid": GESPREK_UUID,
                "file_id": file_id,
            },
        )

    def bestand_requests(self, m):
        return [r for r in m.request_history if "/bestanden/" in r.path]

    def test_the_section_shows_the_bijlage_without_a_call_per_bestand(self, m):
        self.mock_api(m, self.detail)

        content = self.client.get(self.url).content.decode()

        self.assertIn(f'href="{self.bijlage_url()}"', content)
        self.assertIn("loonstrook.pdf", content)
        self.assertIn("(184.32 KB)", content)
        self.assertIn("insert_drive_file", content)
        self.assertEqual(self.bestand_requests(m), [])

    def test_a_bijlage_without_weergavegegevens_is_still_shown(self, m):
        self.detail["gespreksbijdragen"][0]["bijlagen"] = [{"bestand": BESTAND_URL}]
        self.mock_api(m, self.detail)

        content = self.client.get(self.url).content.decode()

        self.assertIn(f'href="{self.bijlage_url()}"', content)
        self.assertIn("Bijlage", content)

    def test_a_bijlage_of_the_gesprek_redirects_to_the_download_url(self, m):
        self.mock_api(m, self.detail)
        m.get(BESTAND_URL, json=bestand(downloadUrl=DOWNLOAD_URL))

        response = self.client.get(self.bijlage_url())

        self.assertRedirects(response, DOWNLOAD_URL, fetch_redirect_response=False)

    def test_a_bestand_that_is_no_bijlage_of_the_gesprek_is_refused(self, m):
        self.mock_api(m, self.detail)

        response = self.client.get(
            self.bijlage_url("ffffffff-ffff-ffff-ffff-ffffffffffff")
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.bestand_requests(m), [])

    def test_a_gesprek_of_another_zaak_is_not_found(self, m):
        self.detail["aanleidingZaak"] = "https://zaken.nl/api/v1/zaken/andere-zaak"
        self.mock_api(m, self.detail)

        self.assertEqual(self.client.get(self.bijlage_url()).status_code, 404)
        self.assertEqual(self.bestand_requests(m), [])

    def test_a_gesprek_without_a_zaak_is_not_found(self, m):
        del self.detail["aanleidingZaak"]
        self.mock_api(m, self.detail)

        self.assertEqual(self.client.get(self.bijlage_url()).status_code, 404)

    def test_a_bestand_without_download_url_is_not_found(self, m):
        self.mock_api(m, self.detail)
        m.get(BESTAND_URL, json=bestand("uploadInAfwachting"))

        self.assertEqual(self.client.get(self.bijlage_url()).status_code, 404)
