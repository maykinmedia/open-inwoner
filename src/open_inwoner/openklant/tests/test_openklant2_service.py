import datetime

from django.test import tag

import freezegun

from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.services import OpenKlant2Question, OpenKlant2Service
from open_inwoner.openklant.tests.helpers import Openklant2ServiceTestCase
from openklant2.factories.partij import CreatePartijPersoonDataFactory
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
            self.persoon["uuid"],
            "telefoon",
            "0644938475",
        )
        self.service.get_or_create_digitaal_adres(
            self.persoon["uuid"],
            "email",
            "bar@foo.com",
        )

        self.service.update_user_from_partij(self.persoon["uuid"], user)
        self.assertEqual(user.phonenumber, "0644938475")
        self.assertEqual(user.email, "bar@foo.com")

    def test_cannot_use_existing_user_email_when_updating_user_from_partij(self):
        user: User = UserFactory(phonenumber="", email="user@bar.com")
        another_user: User = UserFactory(email="another-user@foo.com")

        # Set user's OK email to another user's email
        self.service.get_or_create_digitaal_adres(
            self.persoon["uuid"],
            "email",
            another_user.email,
        )

        self.service.update_user_from_partij(self.persoon["uuid"], user)
        self.assertEqual(
            user.email,
            "user@bar.com",
            msg="Email was not updated to the email in OK due to conflict with existing user",
        )

    def test_update_partij_from_user(self):
        user: User = UserFactory(phonenumber="0644938475", email="user@bar.com")

        self.assertEqual(
            self.service.retrieve_digitale_addressen_for_partij(self.persoon["uuid"]),
            [],
        )

        self.service.update_partij_from_user(self.persoon["uuid"], user)

        self.assertEqual(
            [
                (da["soortDigitaalAdres"], da["adres"])
                for da in self.service.retrieve_digitale_addressen_for_partij(
                    self.persoon["uuid"]
                )
            ],
            [("email", "user@bar.com"), ("telefoon", "0644938475")],
        )


QUESTION_DATE = datetime.datetime(
    2024, 10, 2, 14, 0, 25, 587564, tzinfo=datetime.timezone.utc
)


@tag("openklant2")
@freezegun.freeze_time(QUESTION_DATE)
class QuestionAnswerTestCase(Openklant2ServiceTestCase):
    def setUp(self):
        super().setUp()

        self.designated_actor = self.openklant_client.actor.create(
            data={
                "naam": "Afdeling Klantenservice",
                "soortActor": "organisatorische_eenheid",
                "indicatieActief": True,
            }
        )
        self.een_persoon = self.openklant_client.partij.create_persoon(
            data=CreatePartijPersoonDataFactory(
                partijIdentificatie__contactnaam__voornaam="Alice",
                partijIdentificatie__contactnaam__achternaam="McAlice",
            )
        )
        self.een_ander_persoon = self.openklant_client.partij.create_persoon(
            data=CreatePartijPersoonDataFactory(
                partijIdentificatie__contactnaam__voornaam="Bob",
                partijIdentificatie__contactnaam__achternaam="McBob",
            )
        )

        self.designated_actor = self.openklant_client.actor.create(
            data={
                "naam": "Afdeling klantenservice",
                "indicatieActief": True,
                "soortActor": "organisatorische_eenheid",
            }
        )
        self.service = OpenKlant2Service(
            self.openklant_client, mijn_vragen_actor=self.designated_actor["uuid"]
        )

    def test_designated_actor_is_required_to_create_question(self):
        self.service.mijn_vragen_actor = None

        with self.assertRaises(RuntimeError):
            self.service.create_question(
                self.een_persoon["uuid"],
                question="A question asked by Alice",
                subject="Important questions",
            )

    def test_create_question_raises_on_missing_question(self):
        for question in ("", " ", "   ", "\n", "   \n"):
            with self.subTest("{q=} is not a valid question"):
                with self.assertRaises(ValueError):
                    self.service.create_question(
                        self.een_persoon["uuid"],
                        question=question,
                        subject="Important questions",
                    )

    def test_create_question(self):
        question = self.service.create_question(
            self.een_persoon["uuid"],
            question="A question asked by Alice",
            subject="Important questions",
        )

        # 1 question => 1 klantcontact, 1 betrokkene, 1 taak
        (klantcontact,) = self.service.client.klant_contact.list_iter()
        (betrokkene,) = self.service.client.betrokkene.list_iter()
        (taak,) = self.service.client.interne_taak.list_iter()

        self.assertEqual(klantcontact["kanaal"], self.service.MIJN_VRAGEN_KANAAL)
        self.assertEqual(betrokkene["hadKlantcontact"]["uuid"], klantcontact["uuid"])
        self.assertEqual(betrokkene["wasPartij"]["uuid"], self.een_persoon["uuid"])
        self.assertEqual(
            taak["aanleidinggevendKlantcontact"]["uuid"], klantcontact["uuid"]
        )

        self.assertEqual(
            question,
            OpenKlant2Question(
                answer=None,
                nummer=klantcontact["nummer"],
                question_kcm_uuid=klantcontact["uuid"],
                question="A question asked by Alice",
                plaatsgevonden_op=QUESTION_DATE,
            ),
        )

    def test_get_questions(self):
        for persoon in (self.een_persoon, self.een_ander_persoon):
            raw_questions = [
                self.service.create_question(
                    persoon["uuid"],
                    question=f"A question asked by {persoon['uuid']}, part {i}",
                    subject="Life and stuff",
                )
                for i in range(2)
            ]

            for rq in raw_questions[:1]:
                self.service.create_answer(
                    persoon["uuid"], rq.question_kcm_uuid, "The answer is 42"
                )

        questions = self.service.questions_for_partij(self.een_persoon["uuid"])

        self.assertEqual(
            len(questions), 2, msg="Only the user's questions should be returned"
        )

        self.assertFalse(
            all(
                self.een_ander_persoon["uuid"] in question.question
                for question in questions
            )
        )
        self.assertTrue(
            all(self.een_persoon["uuid"] in question.question for question in questions)
        )
