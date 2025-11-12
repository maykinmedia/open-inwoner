from unittest.mock import Mock, patch

from django.test import TestCase

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.openklant.services import OpenKlant2Service
from open_inwoner.openklant.tests.factories import OpenKlant2ConfigFactory


@patch("open_inwoner.openklant.services.OpenKlantClient")
class UpdateUserFromPartijTestCase(TestCase):
    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def test_email_not_updated_when_already_exists_for_another_user(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Existing user already has email
        UserFactory(email="taken@example.com")

        mock_client.digitaal_adres.list.return_value = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "uuid": "addr-uuid",
                    "soortDigitaalAdres": "email",
                    "adres": "taken@example.com",
                    "isStandaardAdres": True,
                    "omschrijving": "",
                    "verstrektDoorPartij": {"uuid": "partij-uuid"},
                    "verstrektDoorBetrokkene": None,
                }
            ],
        }

        service = OpenKlant2Service(config=self.config)
        user = UserFactory(email="original@example.com")
        service.update_user_from_partij("partij-uuid", user)

        user.refresh_from_db()
        self.assertEqual(
            user.email,
            "original@example.com",
            "Email should not be updated when it conflicts with another user",
        )

    def test_email_updated_when_available(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.digitaal_adres.list.return_value = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "uuid": "addr-uuid",
                    "soortDigitaalAdres": "email",
                    "adres": "available@example.com",
                    "isStandaardAdres": True,
                    "omschrijving": "",
                    "verstrektDoorPartij": {"uuid": "partij-uuid"},
                    "verstrektDoorBetrokkene": None,
                }
            ],
        }

        service = OpenKlant2Service(config=self.config)
        user = UserFactory(email="old@example.com")
        service.update_user_from_partij("partij-uuid", user)

        user.refresh_from_db()
        self.assertEqual(user.email, "available@example.com")

    def test_phone_numbers_mapped_by_standard_flag(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.digitaal_adres.list.return_value = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "uuid": "phone1-uuid",
                    "soortDigitaalAdres": "telefoonnummer",
                    "adres": "0612345678",
                    "isStandaardAdres": True,  # Primary
                    "omschrijving": "",
                    "verstrektDoorPartij": {"uuid": "partij-uuid"},
                    "verstrektDoorBetrokkene": None,
                },
                {
                    "uuid": "phone2-uuid",
                    "soortDigitaalAdres": "telefoonnummer",
                    "adres": "0687654321",
                    "isStandaardAdres": False,  # Alternative
                    "omschrijving": "",
                    "verstrektDoorPartij": {"uuid": "partij-uuid"},
                    "verstrektDoorBetrokkene": None,
                },
            ],
        }

        service = OpenKlant2Service(config=self.config)
        user = UserFactory(phonenumber="", phonenumber_alternative="")
        service.update_user_from_partij("partij-uuid", user)

        user.refresh_from_db()
        self.assertEqual(
            user.phonenumber, "0612345678", "Standard phone should map to primary"
        )
        self.assertEqual(
            user.phonenumber_alternative,
            "0687654321",
            "Non-standard phone should map to alternative",
        )

    def test_logs_warning_when_more_than_two_phone_numbers(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.digitaal_adres.list.return_value = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                {
                    "uuid": f"phone{i}-uuid",
                    "soortDigitaalAdres": "telefoonnummer",
                    "adres": f"06{i}",
                    "isStandaardAdres": i == 0,
                    "omschrijving": "",
                    "verstrektDoorPartij": {"uuid": "partij-uuid"},
                    "verstrektDoorBetrokkene": None,
                }
                for i in range(3)
            ],
        }

        service = OpenKlant2Service(config=self.config)
        user = UserFactory()

        with self.assertLogs(
            "open_inwoner.openklant.services", level="WARNING"
        ) as logs:
            service.update_user_from_partij("partij-uuid", user)

        self.assertTrue(
            any("More than two phone numbers found" in log for log in logs.output),
            "Should log warning when more than 2 phone numbers exist",
        )


@patch("open_inwoner.openklant.services.OpenKlantClient")
class CreateKlantcontactTestCase(TestCase):
    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def test_raises_error_when_question_is_empty(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        for empty_question in ["", "   ", "\n", "  \n  "]:
            with self.subTest(question=repr(empty_question)):
                with self.assertRaises(ValueError) as cm:
                    service._create_klantcontact(
                        question=empty_question, subject="Test subject"
                    )

                self.assertIn("must provide a question", str(cm.exception))

    def test_raises_error_when_actor_not_configured(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Use existing config but override actor
        service = OpenKlant2Service(config=self.config)
        service.config.mijn_vragen_actor = None

        with self.assertRaises(RuntimeError) as cm:
            service._create_klantcontact(question="Valid question", subject="Subject")

        self.assertIn("must define an actor", str(cm.exception))

    def test_creates_klantcontact_with_valid_data(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.klant_contact.create.return_value = {
            "uuid": "kc-uuid",
            "inhoud": "My question",
            "onderwerp": "Subject",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
        }

        service = OpenKlant2Service(config=self.config)
        result = service._create_klantcontact(question="My question", subject="Subject")

        # Verify client was called correctly
        mock_client.klant_contact.create.assert_called_once()
        call_data = mock_client.klant_contact.create.call_args[1]["data"]

        self.assertEqual(call_data["inhoud"], "My question")
        self.assertEqual(call_data["onderwerp"], "Subject")
        self.assertEqual(call_data["kanaal"], self.config.mijn_vragen_kanaal)
        self.assertEqual(call_data["taal"], "nld")

        # Verify return value
        self.assertEqual(result["uuid"], "kc-uuid")


@patch("open_inwoner.openklant.services.OpenKlantClient")
class GetOrCreatePartijForUserTestCase(TestCase):
    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def test_find_existing_persoon_by_bsn(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.partij.list.return_value = {
            "count": 1,
            "results": [{"uuid": "existing-uuid"}],
        }
        mock_client.partij.retrieve.return_value = {
            "uuid": "existing-uuid",
            "soortPartij": "persoon",
            "partijIdentificatie": {
                "contactnaam": {"voornaam": "John", "achternaam": "Doe"}
            },
        }

        service = OpenKlant2Service(config=self.config)
        user = DigidUserFactory(bsn="123456789")

        partij, created = service.get_or_create_partij_for_user(user)

        self.assertFalse(created, "Should retrieve existing partij, not create new")
        self.assertEqual(partij["uuid"], "existing-uuid")

        # Verify searched by BSN
        mock_client.partij.list.assert_called_once()
        call_params = mock_client.partij.list.call_args[1]["params"]
        self.assertEqual(call_params["partijIdentificator__objectId"], "123456789")
        self.assertEqual(call_params["partijIdentificator__codeSoortObjectId"], "bsn")

    def test_create_new_persoon_when_not_found(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.partij.list.return_value = {"count": 0, "results": []}

        mock_client.partij.create_persoon.return_value = {
            "uuid": "new-uuid",
            "soortPartij": "persoon",
            "partijIdentificatie": {
                "contactnaam": {"voornaam": "Jane", "achternaam": "Smith"}
            },
        }

        service = OpenKlant2Service(config=self.config)
        user = DigidUserFactory(first_name="Jane", last_name="Smith", bsn="987654321")

        partij, created = service.get_or_create_partij_for_user(user)

        self.assertTrue(created, "Should create new partij")
        self.assertEqual(partij["uuid"], "new-uuid")

        # Verify creation data includes BSN
        mock_client.partij.create_persoon.assert_called_once()
        call_data = mock_client.partij.create_persoon.call_args[1]["data"]
        self.assertEqual(call_data["soortPartij"], "persoon")
        self.assertEqual(
            call_data["partijIdentificatie"]["contactnaam"]["voornaam"], "Jane"
        )
        self.assertEqual(
            call_data["partijIdentificatie"]["contactnaam"]["achternaam"], "Smith"
        )
        self.assertIn("partijIdentificatoren", call_data)
        self.assertEqual(
            call_data["partijIdentificatoren"][0]["partijIdentificator"]["objectId"],
            "987654321",
        )

    def test_create_persoon_without_identificatoren_when_no_bsn(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.partij.list.return_value = {"count": 0, "results": []}
        mock_client.partij.create_persoon.return_value = {
            "uuid": "no-bsn-uuid",
            "soortPartij": "persoon",
            "partijIdentificatie": {
                "contactnaam": {"voornaam": "Anonymous", "achternaam": "User"}
            },
        }

        service = OpenKlant2Service(config=self.config)
        user = UserFactory(first_name="Anonymous", last_name="User", bsn="", kvk="")

        partij, created = service.get_or_create_partij_for_user(user)

        self.assertTrue(created)
        self.assertEqual(partij["uuid"], "no-bsn-uuid")

        # Verify NO identificatoren in the creation data
        call_data = mock_client.partij.create_persoon.call_args[1]["data"]
        self.assertNotIn(
            "partijIdentificatoren",
            call_data,
            "Should not include identificatoren when user has no BSN",
        )
