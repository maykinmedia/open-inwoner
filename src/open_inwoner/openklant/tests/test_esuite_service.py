from dataclasses import asdict, dataclass

from django.test import TestCase

import requests_mock

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.openklant.api_models import Klant
from open_inwoner.openklant.services import eSuiteKlantenService
from open_inwoner.openklant.tests.data import KLANTEN_ROOT, MockAPIReadData
from open_inwoner.utils.test import DisableRequestLogMixin, paginated_response


class eSuiteServiceTestCase(TestCase, DisableRequestLogMixin):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.data = MockAPIReadData()
        self.data.setUpServices()
        self.service = eSuiteKlantenService()
        self.user = UserFactory()

    def test_create_klant_can_only_specify_valid_identifier_combinations(self):
        for params in (
            # Mutually exclusive
            {
                "user_bsn": "123",
                "user_kvk_or_rsin": "123",
            },
            # Mutually exclusive
            {
                "user_bsn": "123",
                "user_kvk_or_rsin": "123",
                "vestigingsnummer": "123",
            },
            {
                "user_bsn": "123",
                "vestigingsnummer": "123",
            },
            # Needs kvk or rsin
            {
                "vestigingsnummer": "123",
            },
        ):
            with self.subTest(params):
                with self.assertRaises(ValueError):
                    self.service.create_klant(**params)

    def test_create_klant_bsn(self):
        with requests_mock.mock() as m:
            m.post(
                f"{KLANTEN_ROOT}klanten",
                json=self.data.klant_bsn,
            )

            klant = self.service.create_klant(user_bsn="123456789")

        self.assertIsInstance(klant, Klant)
        self.assertEqual(
            m.request_history[0].json(),
            {"subjectIdentificatie": {"inpBsn": "123456789"}},
        )
        self.assertEqual(
            klant,
            Klant(
                url="https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                bronorganisatie="123456789",
                klantnummer="12345678",
                website_url="",
                voornaam="John",
                voorvoegsel_achternaam="van der",
                achternaam="Doe",
                telefoonnummer="0612345678",
                emailadres="foo@example.com",
                toestemming_zaak_notificaties_alleen_digitaal=False,
                bedrijfsnaam="",
            ),
        )

    def test_create_klant_kvk(self):
        with requests_mock.mock() as m:
            m.post(
                f"{KLANTEN_ROOT}klanten",
                json=self.data.klant_kvk,
            )

            klant = self.service.create_klant(user_kvk_or_rsin="87654321")

        self.assertIsInstance(klant, Klant)
        self.assertEqual(
            m.request_history[0].json(),
            {"subjectIdentificatie": {"innNnpId": "87654321"}},
        )
        self.assertEqual(
            klant,
            Klant(
                url="https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-ffffffffffff",
                bronorganisatie="123456789",
                klantnummer="87654321",
                website_url="",
                voornaam="",
                voorvoegsel_achternaam="",
                achternaam="",
                telefoonnummer="0687654321",
                emailadres="foo@bar.com",
                toestemming_zaak_notificaties_alleen_digitaal=False,
                bedrijfsnaam="AcmeCorp B.V.",
            ),
        )

    def test_create_klant_vestigingsnummer(self):
        with requests_mock.mock() as m:
            m.post(
                f"{KLANTEN_ROOT}klanten",
                json=self.data.klant_vestiging,
            )

            klant = self.service.create_klant(
                user_kvk_or_rsin="87654321", vestigingsnummer="123456789000"
            )

        self.assertIsInstance(klant, Klant)
        self.assertEqual(
            m.request_history[0].json(),
            {
                "subjectIdentificatie": {
                    # Note: the innNnpId is not sent for vestiging, it's either innNnpId
                    # or vestigingsNummer
                    "vestigingsNummer": "123456789000",
                }
            },
        )
        self.assertEqual(
            klant,
            Klant(
                url="https://klanten.nl/api/v1/klant/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                bronorganisatie="123456789",
                klantnummer="11111111",
                website_url="",
                voornaam="",
                voorvoegsel_achternaam="",
                achternaam="",
                telefoonnummer="0612345678",
                emailadres="foo@bar.com",
                toestemming_zaak_notificaties_alleen_digitaal=False,
                bedrijfsnaam="AcmeCorp B.V.",
            ),
        )

    def test_retrieve_klant_paginates_full_response(self):
        base_url = f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn={self.data.user.bsn}"

        with requests_mock.mock() as m:
            m.get(
                base_url,
                json=paginated_response([self.data.klant_bsn])
                | {"next": f"{base_url}&page=2"},
            )
            m.get(
                f"{base_url}&page=2",
                json=paginated_response([self.data.klant_kvk])
                | {"next": f"{base_url}&page=3"},
            )
            m.get(
                f"{base_url}&page=3",
                json=paginated_response([self.data.klant_vestiging]),  # next=None
            )

            # Paginates all responses that match the BSN
            klant = self.service.retrieve_klant(user_bsn=self.data.user.bsn)

        self.assertEqual(
            klant,
            Klant(
                url="https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                bronorganisatie="123456789",
                klantnummer="12345678",
                website_url="",
                voornaam="John",
                voorvoegsel_achternaam="van der",
                achternaam="Doe",
                telefoonnummer="0612345678",
                telefoonnummerAlternatief="",
                emailadres="foo@example.com",
                toestemming_zaak_notificaties_alleen_digitaal=False,
                bedrijfsnaam="",
            ),
        )

        self.assertEqual(
            [rh.url for rh in m.request_history],
            [
                base_url,
                f"{base_url}&page=2",
                f"{base_url}&page=3",
            ],
        )

    def test_update_klant_from_user(self):
        user = DigidUserFactory(
            email="old@example.com",
            phonenumber="0100000000",
            phonenumber_alternative="",
        )

        @dataclass
        class Klant:
            bronorganisatie: str
            klantnummer: str
            subjectIdentificatie: str
            url: str
            emailadres: str
            telefoonnummer: str
            telefoonnummerAlternatief: str
            toestemmingZaakNotificatiesAlleenDigitaal: str

        klant = Klant(
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "inpBsn": "123456789",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="old@example.com",
            telefoonnummer="0100000000",
            telefoonnummerAlternatief="0687654321",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )

        with requests_mock.mock() as m:
            m.patch(klant.url, json=asdict(klant))

            klant = self.service.update_klant_from_user(
                klant,
                user,
                update_fields=["telefoonnummer", "telefoonnummerAlternatief"],
            )

            self.assertEqual(klant.telefoonnummerAlternatief, "")
