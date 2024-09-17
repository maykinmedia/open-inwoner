from django.test import tag

from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.services import OpenKlant2Service
from open_inwoner.openklant.tests.helpers import Openklant2ServiceTestCase
from openklant2.types.resources.partij import PartijValidator


@tag("openklant2")
class PartijGetOrCreateTestCase(Openklant2ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.service = OpenKlant2Service(self.openklant_client)
        self.user = UserFactory(first_name="John", last_name="Doe")

    def test_get_or_create_persoon(self):
        # Empty state
        self.assertEqual(self.service.client.partij.list()["count"], 0)
        self.assertEqual(self.service.client.partij_identificator.list()["count"], 0)

        # First call creates
        persoon = self.service.get_or_create_partij_for_user(
            {"user_bsn": "123456789"}, self.user
        )

        PartijValidator.validate_python(persoon)
        self.assertEqual(self.service.client.partij.list()["count"], 1)
        self.assertEqual(
            [
                row["partijIdentificator"]
                for row in self.service.client.partij_identificator.list()["results"]
            ],
            [
                {
                    "codeObjecttype": "inp",
                    "codeSoortObjectId": "bsn",
                    "objectId": "123456789",
                    "codeRegister": "brp",
                }
            ],
        )

        # Second call gets
        persoon = self.service.get_or_create_partij_for_user(
            {"user_bsn": "123456789"}, self.user
        )

        PartijValidator.validate_python(persoon)
        self.assertEqual(self.service.client.partij.list()["count"], 1)
        self.assertEqual(
            [
                row["partijIdentificator"]
                for row in self.service.client.partij_identificator.list()["results"]
            ],
            [
                {
                    "codeObjecttype": "inp",
                    "codeSoortObjectId": "bsn",
                    "objectId": "123456789",
                    "codeRegister": "brp",
                }
            ],
        )

    def test_get_or_create_organisatie_without_vestiging(self):
        # Empty state
        self.assertEqual(self.service.client.partij.list()["count"], 0)
        self.assertEqual(self.service.client.partij_identificator.list()["count"], 0)

        # First call creates
        persoon = self.service.get_or_create_partij_for_user(
            {"user_kvk_or_rsin": "123456789"},
            self.user,
        )

        PartijValidator.validate_python(persoon)
        self.assertEqual(self.service.client.partij.list()["count"], 1)
        self.assertEqual(
            [
                row["partijIdentificator"]
                for row in self.service.client.partij_identificator.list()["results"]
            ],
            [
                {
                    "codeObjecttype": "nnp",
                    "codeSoortObjectId": "kvk",
                    "objectId": "123456789",
                    "codeRegister": "hr",
                },
            ],
        )

        # Second call gets
        persoon = self.service.get_or_create_partij_for_user(
            {"user_kvk_or_rsin": "123456789"}, self.user
        )

        PartijValidator.validate_python(persoon)
        self.assertEqual(self.service.client.partij.list()["count"], 1)
        self.assertEqual(
            [
                row["partijIdentificator"]
                for row in self.service.client.partij_identificator.list()["results"]
            ],
            [
                {
                    "codeObjecttype": "nnp",
                    "codeSoortObjectId": "kvk",
                    "objectId": "123456789",
                    "codeRegister": "hr",
                }
            ],
        )

    def test_get_or_create_organisatie_with_vestiging(self):
        # Empty state
        self.assertEqual(self.service.client.partij.list()["count"], 0)
        self.assertEqual(self.service.client.partij_identificator.list()["count"], 0)

        # First call creates
        persoon = self.service.get_or_create_partij_for_user(
            {"user_kvk_or_rsin": "123456789", "vestigingsnummer": "987654321"},
            self.user,
        )

        PartijValidator.validate_python(persoon)
        self.assertEqual(self.service.client.partij.list()["count"], 1)
        self.assertEqual(
            [
                row["partijIdentificator"]
                for row in self.service.client.partij_identificator.list()["results"]
            ],
            [
                {
                    "codeObjecttype": "nnp",
                    "codeSoortObjectId": "vtn",
                    "objectId": "987654321",
                    "codeRegister": "hr",
                },
                {
                    "codeObjecttype": "nnp",
                    "codeSoortObjectId": "kvk",
                    "objectId": "123456789",
                    "codeRegister": "hr",
                },
            ],
        )

        # Second call gets
        persoon = self.service.get_or_create_partij_for_user(
            {"user_kvk_or_rsin": "123456789"}, self.user
        )

        PartijValidator.validate_python(persoon)
        self.assertEqual(self.service.client.partij.list()["count"], 1)
        self.assertEqual(
            [
                row["partijIdentificator"]
                for row in self.service.client.partij_identificator.list()["results"]
            ],
            [
                {
                    "codeObjecttype": "nnp",
                    "codeSoortObjectId": "vtn",
                    "objectId": "987654321",
                    "codeRegister": "hr",
                },
                {
                    "codeObjecttype": "nnp",
                    "codeSoortObjectId": "kvk",
                    "objectId": "123456789",
                    "codeRegister": "hr",
                },
            ],
        )


@tag("openklant2")
class Openklant2ServiceTest(Openklant2ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.service = OpenKlant2Service(self.openklant_client)

        self.persoon = self.openklant_client.partij.create_persoon(
            data={
                "digitaleAdressen": None,
                "voorkeursDigitaalAdres": None,
                "rekeningnummers": None,
                "voorkeursRekeningnummer": None,
                "indicatieGeheimhouding": False,
                "indicatieActief": True,
                "voorkeurstaal": "crp",
                "soortPartij": "persoon",
                "partijIdentificatie": {
                    "contactnaam": {
                        "voorletters": "Dr.",
                        "voornaam": "Test Persoon",
                        "voorvoegselAchternaam": "Mrs.",
                        "achternaam": "Gamble",
                    }
                },
            }
        )
        self.openklant_client.partij_identificator.create(
            data={
                "identificeerdePartij": {"uuid": self.persoon["uuid"]},
                "partijIdentificator": {
                    "codeObjecttype": "bsn",
                    "codeSoortObjectId": "inp",
                    "objectId": "123456789",
                    "codeRegister": "brp",
                },
                "anderePartijIdentificator": "optional_identifier_123",
            }
        )

    def test_update_user_from_partij(self):
        user: User = UserFactory(phonenumber="", email="foo@bar.com")
        self.service.get_or_create_digitaal_adres(
            self.persoon,
            "telefoon",
            "0644938475",
        )
        self.service.get_or_create_digitaal_adres(
            self.persoon,
            "email",
            "bar@foo.com",
        )

        self.service.update_user_from_partij(self.persoon, user)
        self.assertEqual(user.phonenumber, "0644938475")
        self.assertEqual(user.email, "bar@foo.com")

    def test_cannot_use_existing_user_email_when_updating_user_from_partij(self):
        user: User = UserFactory(phonenumber="", email="user@bar.com")
        another_user: User = UserFactory(email="another-user@foo.com")

        # Set user's OK email to another user's email
        self.service.get_or_create_digitaal_adres(
            self.persoon,
            "email",
            another_user.email,
        )

        self.service.update_user_from_partij(self.persoon, user)
        self.assertEqual(
            user.email,
            "user@bar.com",
            msg="Email was not updated to the email in OK due to conflict with existing user",
        )

    def test_update_partij_from_user(self):
        user: User = UserFactory(phonenumber="0644938475", email="user@bar.com")

        self.assertEqual(
            self.service.retrieve_digitale_addressen_for_partij(self.persoon),
            [],
        )

        self.service.update_partij_from_user(self.persoon, user)

        self.assertEqual(
            [
                (da["soortDigitaalAdres"], da["adres"])
                for da in self.service.retrieve_digitale_addressen_for_partij(
                    self.persoon
                )
            ],
            [("email", "user@bar.com"), ("telefoon", "0644938475")],
        )
