from dataclasses import asdict

from django.test import TestCase

import requests_mock

from open_inwoner.accounts.choices import DigitalAddressType
from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    DigitalAddressFactory,
    UserFactory,
)
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
                telefoonnummer_alternatief="0687654321",
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
                telefoonnummer_alternatief="0687654321",
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
                    "innNnpId": "87654321",
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
                telefoonnummer_alternatief="0687654321",
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
                telefoonnummer_alternatief="0687654321",
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

        klant = Klant(
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            bronorganisatie="123456789",
            klantnummer="12345678",
            emailadres="old@example.com",
            telefoonnummer="0100000000",
            telefoonnummer_alternatief="0687654321",
        )

        with requests_mock.mock() as m:
            m.patch(klant.url, json=asdict(klant))

            self.service.update_klant_from_user(
                klant,
                user,
                update_fields=["telefoonnummer", "telefoonnummerAlternatief"],
            )

            self.assertIsNone(m.last_request.json()["telefoonnummerAlternatief"])

    def test_update_klant_from_user_sends_alternative_phone_from_digital_address(self):
        user = DigidUserFactory(
            phonenumber="0611111111",
            phonenumber_alternative="0655555555",
        )

        klant = Klant(
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            bronorganisatie="123456789",
            klantnummer="12345678",
            emailadres=user.email,
            telefoonnummer="0611111111",
            telefoonnummer_alternatief="0622222222",
        )

        with requests_mock.mock() as m:
            m.patch(klant.url, json=asdict(klant))

            self.service.update_klant_from_user(
                klant,
                user,
                update_fields=["telefoonnummerAlternatief"],
            )

            self.assertEqual(
                m.request_history[0].json()["telefoonnummerAlternatief"],
                "0655555555",
            )

    def _make_klant(self, telefoonnummer="", telefoonnummer_alternatief=""):
        return Klant(
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            bronorganisatie="123456789",
            klantnummer="12345678",
            telefoonnummer=telefoonnummer,
            telefoonnummer_alternatief=telefoonnummer_alternatief,
        )

    def test_update_user_from_klant_clears_alternative_when_same_as_primary_in_klant(
        self,
    ):
        """If klant sends the same number for both fields, alternative is dropped."""
        user = DigidUserFactory(phonenumber="0100000000", phonenumber_alternative="")
        klant = self._make_klant(
            telefoonnummer="0611111111",
            telefoonnummer_alternatief="0611111111",
        )

        self.service.update_user_from_klant(klant, user)

        user.refresh_from_db()
        self.assertEqual(user.phonenumber, "0611111111")
        self.assertEqual(user.phonenumber_alternative, "")

    def test_update_user_from_klant_clears_alternative_when_primary_updated_to_match_it(
        self,
    ):
        """If klant's primary number matches the user's existing alternative, alternative is dropped."""
        user = DigidUserFactory(
            phonenumber="0100000000", phonenumber_alternative="0611111111"
        )
        klant = self._make_klant(
            telefoonnummer="0611111111",
            telefoonnummer_alternatief="0611111111",
        )

        self.service.update_user_from_klant(klant, user)

        user.refresh_from_db()
        self.assertEqual(user.phonenumber, "0611111111")
        self.assertEqual(user.phonenumber_alternative, "")


class UpdateUserFromKlantDigitalAddressTestCase(TestCase, DisableRequestLogMixin):
    def setUp(self):
        super().setUp()
        self.data = MockAPIReadData()
        self.data.setUpServices()
        self.service = eSuiteKlantenService()

    def _make_klant(
        self, emailadres="", telefoonnummer="", telefoonnummer_alternatief=""
    ):
        return Klant(
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            bronorganisatie="123456789",
            klantnummer="12345678",
            emailadres=emailadres,
            telefoonnummer=telefoonnummer,
            telefoonnummer_alternatief=telefoonnummer_alternatief,
        )

    def test_inbound_email_creates_standard_digital_address(self):
        user = DigidUserFactory(email="old@example.com")
        klant = self._make_klant(emailadres="new@example.com")

        self.service.update_user_from_klant(klant, user)

        da = user.digital_addresses.get(type=DigitalAddressType.email)
        self.assertEqual(da.value, "new@example.com")
        self.assertTrue(da.is_standard_for_type)

    def test_inbound_primary_phone_creates_standard_digital_address(self):
        user = DigidUserFactory(phonenumber="0600000000")
        klant = self._make_klant(telefoonnummer="0611111111")

        self.service.update_user_from_klant(klant, user)

        da = user.digital_addresses.get(
            type=DigitalAddressType.phone, is_standard_for_type=True
        )
        self.assertEqual(da.value, "0611111111")

    def test_inbound_alternative_phone_creates_non_standard_digital_address(self):
        user = DigidUserFactory(phonenumber="0611111111", phonenumber_alternative="")
        klant = self._make_klant(
            telefoonnummer="0611111111",
            telefoonnummer_alternatief="0622222222",
        )

        self.service.update_user_from_klant(klant, user)

        da = user.digital_addresses.get(
            type=DigitalAddressType.phone, is_standard_for_type=False
        )
        self.assertEqual(da.value, "0622222222")

    def test_inbound_alternative_phone_deleted_when_esuite_removes_it(self):
        user = DigidUserFactory(
            phonenumber="0611111111", phonenumber_alternative="0622222222"
        )
        klant = self._make_klant(
            telefoonnummer="0611111111",
            telefoonnummer_alternatief="",
        )

        self.service.update_user_from_klant(klant, user)

        self.assertFalse(
            user.digital_addresses.filter(
                type=DigitalAddressType.phone, is_standard_for_type=False
            ).exists()
        )

    def test_inbound_alternative_phone_replaced_when_esuite_changes_it(self):
        user = DigidUserFactory(
            phonenumber="0611111111", phonenumber_alternative="0622222222"
        )
        klant = self._make_klant(
            telefoonnummer="0611111111",
            telefoonnummer_alternatief="0633333333",
        )

        self.service.update_user_from_klant(klant, user)

        alts = list(
            user.digital_addresses.filter(
                type=DigitalAddressType.phone, is_standard_for_type=False
            ).values_list("value", flat=True)
        )
        self.assertEqual(alts, ["0633333333"])

    def test_push_back_standard_email_when_esuite_has_no_email(self):
        user = DigidUserFactory(email="user@example.com")
        DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value="user@example.com",
            is_standard_for_type=True,
        )
        klant = self._make_klant(emailadres="")

        with requests_mock.mock() as m:
            m.patch(klant.url, json=self.data.klant_bsn)
            self.service.update_user_from_klant(klant, user)

        self.assertEqual(len(m.request_history), 1)
        self.assertEqual(m.request_history[0].json()["emailadres"], "user@example.com")

    def test_no_push_back_when_esuite_has_email(self):
        user = DigidUserFactory(email="user@example.com")
        klant = self._make_klant(emailadres="user@example.com")

        with requests_mock.mock() as m:
            m.patch(klant.url, json=self.data.klant_bsn)
            self.service.update_user_from_klant(klant, user)

        self.assertEqual(len(m.request_history), 0)
