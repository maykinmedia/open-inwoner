import datetime
import logging

from django.test import tag

import freezegun
from timeline_logger.models import TimelineLog

from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    UserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
)
from open_inwoner.openklant.services import OpenKlant2Question, OpenKlant2Service
from open_inwoner.openklant.tests.factories import OpenKlant2ConfigFactory
from open_inwoner.openklant.tests.helpers import Openklant2ServiceTestCase
from openklant2.factories.partij import CreatePartijPersoonDataFactory
from openklant2.types.resources.partij import PartijValidator


@tag("openklant2")
class PartijGetOrCreateTestCase(Openklant2ServiceTestCase):
    def setUp(self):
        super().setUp()

        self.openklant2_config = OpenKlant2ConfigFactory()
        self.service = OpenKlant2Service(config=self.openklant2_config)
        self.digid_user = DigidUserFactory(
            first_name="John", last_name="Doe", bsn="521311408"
        )
        self.kvk_only_user = eHerkenningUserFactory(kvk="12345678")
        self.vestiging_user = eHerkenningVestigingUserFactory(
            kvk=self.kvk_only_user.kvk, vestiging="123456789123"
        )

    def test_get_or_create_persoon(self):
        # Empty state
        self.assertEqual(self.service.client.partij.list()["count"], 0)
        self.assertEqual(self.service.client.partij_identificator.list()["count"], 0)

        # First call creates
        persoon, created = self.service.get_or_create_partij_for_user(self.digid_user)

        self.assertTrue(
            created, "persoon was retrieved (GET), expected create via POST"
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
                    "codeObjecttype": "natuurlijk_persoon",
                    "codeSoortObjectId": "bsn",
                    "objectId": "521311408",
                    "codeRegister": "brp",
                }
            ],
        )

        # Second call gets
        persoon, created = self.service.get_or_create_partij_for_user(self.digid_user)

        self.assertFalse(
            created, "persoon was was created (POST), expected retrieve via GET"
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
                    "codeObjecttype": "natuurlijk_persoon",
                    "codeSoortObjectId": "bsn",
                    "objectId": "521311408",
                    "codeRegister": "brp",
                }
            ],
        )

    def test_get_or_create_organisatie_without_vestiging(self):
        # Empty state
        self.assertEqual(self.service.client.partij.list()["count"], 0)
        self.assertEqual(self.service.client.partij_identificator.list()["count"], 0)

        # First call creates
        persoon, created = self.service.get_or_create_partij_for_user(
            self.kvk_only_user
        )

        self.assertTrue(
            created, "persoon was retrieved (GET), expected create via POST"
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
                    "codeObjecttype": "niet_natuurlijk_persoon",
                    "codeSoortObjectId": "kvk_nummer",
                    "objectId": "12345678",
                    "codeRegister": "hr",
                },
            ],
        )

        # Second call gets
        persoon, created = self.service.get_or_create_partij_for_user(
            self.kvk_only_user
        )

        self.assertFalse(
            created, "persoon was was created (POST), expected retrieve via GET"
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
                    "codeObjecttype": "niet_natuurlijk_persoon",
                    "codeSoortObjectId": "kvk_nummer",
                    "objectId": "12345678",
                    "codeRegister": "hr",
                }
            ],
        )

    def test_get_or_create_organisatie_with_vestiging(self):
        # Empty state
        self.assertEqual(self.service.client.partij.list()["count"], 0)
        self.assertEqual(self.service.client.partij_identificator.list()["count"], 0)

        # First call creates
        persoon, created = self.service.get_or_create_partij_for_user(
            self.vestiging_user,
        )

        self.assertTrue(
            created, "persoon was retrieved (GET), expected create via POST"
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
                    "codeObjecttype": "vestiging",
                    "codeSoortObjectId": "vestigingsnummer",
                    "objectId": "123456789123",
                    "codeRegister": "hr",
                },
                {
                    "codeObjecttype": "niet_natuurlijk_persoon",
                    "codeSoortObjectId": "kvk_nummer",
                    "objectId": "12345678",
                    "codeRegister": "hr",
                },
            ],
        )

        # Second call gets
        persoon, created = self.service.get_or_create_partij_for_user(
            self.vestiging_user
        )

        self.assertFalse(
            created, "persoon was was created (POST), expected retrieve via GET"
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
                    "codeObjecttype": "vestiging",
                    "codeSoortObjectId": "vestigingsnummer",
                    "objectId": "123456789123",
                    "codeRegister": "hr",
                },
                {
                    "codeObjecttype": "niet_natuurlijk_persoon",
                    "codeSoortObjectId": "kvk_nummer",
                    "objectId": "12345678",
                    "codeRegister": "hr",
                },
            ],
        )


@tag("openklant2")
class Openklant2ServiceTest(Openklant2ServiceTestCase):
    def setUp(self):
        super().setUp()

        self.openklant2_config = OpenKlant2ConfigFactory()
        self.service = OpenKlant2Service(config=self.openklant2_config)

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
                    "codeObjecttype": "natuurlijk_persoon",
                    "codeSoortObjectId": "bsn",
                    "objectId": "521311408",
                    "codeRegister": "brp",
                },
                "anderePartijIdentificator": "optional_identifier_123",
            }
        )

    def test_update_user_from_partij(self):
        user: User = UserFactory(phonenumber="", email="foo@bar.com")
        self.service.get_or_create_digitaal_adres(
            self.persoon["uuid"],
            "telefoonnummer",
            "0644938475",
            is_standaard_adres=True,
        )
        # bogus address for testing edge case with multiple non-standard numbers
        self.service.get_or_create_digitaal_adres(
            self.persoon["uuid"],
            "telefoonnummer",
            "0612345678",
            is_standaard_adres=False,
        )
        self.service.get_or_create_digitaal_adres(
            self.persoon["uuid"],
            "telefoonnummer",
            "0687654321",
            is_standaard_adres=False,
        )
        self.service.get_or_create_digitaal_adres(
            self.persoon["uuid"],
            "email",
            "bar@foo.com",
        )

        logger = logging.getLogger("open_inwoner.openklant.services")

        with self.assertLogs(logger=logger) as logs:
            self.service.update_user_from_partij(self.persoon["uuid"], user)

            self.assertEqual(len(logs.output), 1)
            self.assertIn(
                f"More than two phone numbers found for partij {self.persoon['uuid']}",
                logs.output[0],
            )

        self.assertEqual(user.phonenumber, "0644938475")
        self.assertEqual(user.phonenumber_alternative, "0687654321")
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
        user: User = UserFactory(
            phonenumber="0644938475",
            phonenumber_alternative="0687654321",
            email="user@bar.com",
        )

        self.assertEqual(
            self.service.retrieve_digitale_addressen_for_partij(self.persoon["uuid"]),
            [],
        )

        self.service.update_partij_from_user(self.persoon["uuid"], user)

        adressen = self.service.retrieve_digitale_addressen_for_partij(
            self.persoon["uuid"]
        )

        self.assertEqual(
            set([(adres["soortDigitaalAdres"], adres["adres"]) for adres in adressen]),
            {
                ("email", "user@bar.com"),
                ("telefoonnummer", "0644938475"),
                ("telefoonnummer", "0687654321"),
            },
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

        self.openklant2_config = OpenKlant2ConfigFactory(
            mijn_vragen_actor=self.designated_actor["uuid"]
        )
        self.service = OpenKlant2Service(config=self.openklant2_config)

    def test_designated_actor_is_required_to_create_question(self):
        self.openklant2_config.mijn_vragen_actor = None

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

        self.assertEqual(
            klantcontact["kanaal"], self.openklant2_config.mijn_vragen_kanaal
        )
        self.assertEqual(betrokkene["hadKlantcontact"]["uuid"], klantcontact["uuid"])
        self.assertEqual(betrokkene["wasPartij"]["uuid"], self.een_persoon["uuid"])
        self.assertEqual(
            taak["aanleidinggevendKlantcontact"]["uuid"], klantcontact["uuid"]
        )

        self.assertEqual(
            question,
            OpenKlant2Question(
                url=klantcontact["url"],
                answer=None,
                nummer=klantcontact["nummer"],
                question_kcm_uuid=klantcontact["uuid"],
                question="A question asked by Alice",
                onderwerp="Important questions",
                kanaal=self.openklant2_config.mijn_vragen_kanaal,
                taal="nld",
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

    def test_create_question_for_zaak(self):
        class MockZaak:
            def __init__(self, identificatie):
                self.identificatie = identificatie

        zaak = MockZaak(identificatie="Coffee zaak")
        question = self.service.create_question_for_zaak(
            self.een_persoon["uuid"],
            question="A question asked by Morice",
            subject="Important question",
            zaak=zaak,
        )

        # check onderwerp_object created
        onderwerp_objecten = self.service.client.onderwerp_object.list()
        self.assertEqual(len(onderwerp_objecten["results"]), 1)

        onderwerp_object = onderwerp_objecten["results"][0]
        self.assertEqual(
            onderwerp_object["klantcontact"]["uuid"], question.question_kcm_uuid
        )

        # check logs
        log_entries = TimelineLog.objects.all()

        self.assertEqual(log_entries.count(), 2)
        self.assertEqual(
            log_entries[0].extra_data["message"],
            f"registered question {question.question_kcm_uuid} for partij {self.een_persoon['uuid']} via OpenKlant",
        )
        self.assertEqual(
            log_entries[1].extra_data["message"],
            f"Created onderwerp_object {onderwerp_object['uuid']} for zaak `{zaak.identificatie}`",
        )
