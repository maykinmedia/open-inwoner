import datetime as dt
import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

import requests_mock

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.gesprekken.client import GesprekkenAPIError
from open_inwoner.gesprekken.models import GesprekGezien
from open_inwoner.gesprekken.services import resident_email
from open_inwoner.gesprekken.tasks import MAIL_TEMPLATE, send_gesprek_bijdrage_email
from open_inwoner.openklant.tests.factories import OpenKlant2ConfigFactory
from open_inwoner.utils.test import ClearCachesMixin, paginated_response

from .shared import GESPREK_URL, PARTIJ_UUID, ZAAK_URL, gesprek_detail

GELEVERD = timezone.make_aware(dt.datetime(2026, 7, 13, 7, 30))


@patch("open_inwoner.gesprekken.tasks.send_case_update_email")
@patch("open_inwoner.gesprekken.tasks._get_initiator_users_from_roles")
@patch("open_inwoner.gesprekken.tasks.ZGWService")
@patch(
    "open_inwoner.gesprekken.tasks.ZGWApiGroupConfig.objects.resolve_group_from_hints"
)
class SendGesprekBijdrageEmailTests(TestCase):
    def setUp(self):
        self.user = DigidUserFactory(bsn="100000001", email="piet@example.com")
        client = patch("open_inwoner.gesprekken.tasks.build_gesprekken_client")
        self.client = client.start()
        self.addCleanup(client.stop)
        self.client.return_value.get_gesprek.return_value = gesprek_detail()

    def run_task(self, resolve, zgw_service, users, send, *, gebruikers):
        resolve.return_value = MagicMock()
        zgw_service.return_value.fetch_zaak_by_url.return_value = MagicMock()
        users.return_value = gebruikers
        return send_gesprek_bijdrage_email(GESPREK_URL, ZAAK_URL, GELEVERD.isoformat())

    def test_the_resident_is_emailed_when_the_bijdrage_was_not_seen(
        self, resolve, zgw_service, users, send
    ):
        result = self.run_task(
            resolve, zgw_service, users, send, gebruikers=[self.user]
        )

        send.assert_called_once()
        self.assertEqual(send.call_args.args[0], self.user)
        self.assertEqual(send.call_args.args[2], MAIL_TEMPLATE)
        # Without Klantinteracties: the address in the profile
        self.assertEqual(send.call_args.kwargs["recipient"], "piet@example.com")
        self.assertEqual(result, "sent 1 e-mail(s)")

    def test_no_email_when_the_resident_saw_the_gesprek_afterwards(
        self, resolve, zgw_service, users, send
    ):
        GesprekGezien.objects.create(
            user=self.user,
            gesprek_url=GESPREK_URL,
            gezien_op=GELEVERD + dt.timedelta(minutes=2),
        )

        self.run_task(resolve, zgw_service, users, send, gebruikers=[self.user])

        send.assert_not_called()

    def test_an_earlier_visit_does_not_count(self, resolve, zgw_service, users, send):
        GesprekGezien.objects.create(
            user=self.user,
            gesprek_url=GESPREK_URL,
            gezien_op=GELEVERD - dt.timedelta(days=1),
        )

        self.run_task(resolve, zgw_service, users, send, gebruikers=[self.user])

        send.assert_called_once()

    def test_no_email_when_the_resident_turned_off_case_notifications(
        self, resolve, zgw_service, users, send
    ):
        self.user.cases_notifications = False
        self.user.save()

        result = self.run_task(
            resolve, zgw_service, users, send, gebruikers=[self.user]
        )

        send.assert_not_called()
        self.assertEqual(result, "sent 0 e-mail(s)")

    @patch("open_inwoner.gesprekken.tasks.resident_email", return_value="x@example.com")
    @patch("open_inwoner.gesprekken.tasks.resolve_partij_uuid")
    def test_only_users_taking_part_in_the_gesprek_are_emailed(
        self, partij_uuid, _email, resolve, zgw_service, users, send
    ):
        OpenKlant2ConfigFactory()
        gemachtigde = DigidUserFactory(bsn="100000002", email="gemachtigde@example.com")
        partij_uuid.side_effect = lambda user: (
            PARTIJ_UUID if user == self.user else "dddddddd-dddd-dddd-dddd-dddddddddddd"
        )

        self.run_task(
            resolve, zgw_service, users, send, gebruikers=[gemachtigde, self.user]
        )

        send.assert_called_once()
        self.assertEqual(send.call_args.args[0], self.user)

    def test_no_email_when_the_gesprek_cannot_be_retrieved(
        self, resolve, zgw_service, users, send
    ):
        self.client.return_value.get_gesprek.side_effect = GesprekkenAPIError()

        result = self.run_task(
            resolve, zgw_service, users, send, gebruikers=[self.user]
        )

        send.assert_not_called()
        self.assertEqual(result, "ignored: cannot retrieve gesprek")

    def test_residents_without_email_are_skipped(
        self, resolve, zgw_service, users, send
    ):
        zonder_email = DigidUserFactory(bsn="100000002", email="")

        self.run_task(resolve, zgw_service, users, send, gebruikers=[zonder_email])

        send.assert_not_called()

    def test_a_generated_placeholder_address_is_not_used(
        self, resolve, zgw_service, users, send
    ):
        gegenereerd = DigidUserFactory(bsn="100000003", email="100000003@localhost")

        self.run_task(resolve, zgw_service, users, send, gebruikers=[gegenereerd])

        send.assert_not_called()


KLANTINTERACTIES_ROOT = "https://klantinteracties.example.nl/api/v1/"


def digitaal_adres(adres: str, soort: str = "email", standaard: bool = False) -> dict:
    adres_uuid = str(uuid.uuid4())
    return {
        "uuid": adres_uuid,
        "url": f"{KLANTINTERACTIES_ROOT}digitaleadressen/{adres_uuid}",
        "soortDigitaalAdres": soort,
        "adres": adres,
        "isStandaardAdres": standaard,
        "omschrijving": "",
        "referentie": "",
        "verstrektDoorPartij": {
            "uuid": PARTIJ_UUID,
            "url": f"{KLANTINTERACTIES_ROOT}partijen/{PARTIJ_UUID}",
        },
        "verstrektDoorBetrokkene": None,
    }


@requests_mock.Mocker()
class ResidentEmailTests(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = DigidUserFactory(bsn="100000001", email="profiel@example.com")
        OpenKlant2ConfigFactory(service__api_root=KLANTINTERACTIES_ROOT)
        partij = patch(
            "open_inwoner.openklant.services.OpenKlant2Service.get_partij_for_user",
            return_value={"uuid": PARTIJ_UUID},
        )
        self.partij_lookup = partij.start()
        self.addCleanup(partij.stop)

    def mock_adressen(self, m, *adressen):
        m.get(
            f"{KLANTINTERACTIES_ROOT}digitaleadressen",
            json=paginated_response(list(adressen)),
            headers={"Content-Type": "application/json"},
        )

    def test_the_address_comes_from_the_partij_with_the_standard_address_first(self, m):
        self.mock_adressen(
            m,
            digitaal_adres("0612345678", soort="telefoonnummer", standaard=True),
            digitaal_adres("oud@example.com"),
            digitaal_adres("partij@example.com", standaard=True),
        )

        self.assertEqual(resident_email(self.user), "partij@example.com")
        self.assertEqual(m.last_request.qs["verstrektdoorpartij__uuid"], [PARTIJ_UUID])

    def test_any_email_address_of_the_partij_goes_before_the_profile(self, m):
        self.mock_adressen(m, digitaal_adres("partij@example.com"))

        self.assertEqual(resident_email(self.user), "partij@example.com")

    def test_fallback_without_an_email_address_at_the_partij(self, m):
        self.mock_adressen(m, digitaal_adres("0612345678", soort="telefoonnummer"))

        self.assertEqual(resident_email(self.user), "profiel@example.com")

    def test_fallback_without_a_partij(self, m):
        self.partij_lookup.return_value = None

        self.assertEqual(resident_email(self.user), "profiel@example.com")
        self.assertEqual(m.call_count, 0)

    def test_fallback_when_klantinteracties_fails(self, m):
        m.get(f"{KLANTINTERACTIES_ROOT}digitaleadressen", status_code=500)

        self.assertEqual(resident_email(self.user), "profiel@example.com")


class ResidentEmailWithoutKlantinteractiesTests(TestCase):
    def test_fallback_without_a_klanten_api(self):
        user = DigidUserFactory(bsn="100000001", email="profiel@example.com")

        self.assertEqual(resident_email(user), "profiel@example.com")
