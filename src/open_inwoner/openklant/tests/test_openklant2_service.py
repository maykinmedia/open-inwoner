import datetime
from unittest.mock import Mock, call, patch

from django.test import TestCase

from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.openklant.services import (
    OpenKlant2Answer,
    OpenKlant2Question,
    OpenKlant2Service,
)
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


@patch("open_inwoner.openklant.services.OpenKlantClient")
class OpenKlant2QuestionAnswerTestCase(TestCase):
    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def test_answer_property_returns_none_when_no_answers(self, mock_client_class):
        question = OpenKlant2Question(
            url="http://example.com/question/1",
            question="What is the final answer?",
            question_kcm_uuid="q-uuid-1",
            onderwerp="Philosophy",
            kanaal="online",
            taal="nld",
            nummer="0001",
            plaatsgevonden_op=datetime.datetime(
                2024, 10, 2, 14, 0, 0, tzinfo=datetime.timezone.utc
            ),
            answers=[],
        )

        self.assertIsNone(question.answer)

    def test_answer_property_returns_newest(self, mock_client_class):
        """
        Verify that the field_validator automatically sorts answers by datetime (newest first).
        """
        answer_old = OpenKlant2Answer(
            answer="First answer",
            answer_kcm_uuid="a-uuid-1",
            nummer="0002",
            plaatsgevonden_op=datetime.datetime(
                2024, 10, 2, 14, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
        answer_middle = OpenKlant2Answer(
            answer="Updated answer",
            answer_kcm_uuid="a-uuid-2",
            nummer="0003",
            plaatsgevonden_op=datetime.datetime(
                2025, 10, 2, 14, 30, 0, tzinfo=datetime.timezone.utc
            ),
        )
        answer_new = OpenKlant2Answer(
            answer="Final answer",
            answer_kcm_uuid="a-uuid-3",
            nummer="0004",
            plaatsgevonden_op=datetime.datetime(
                2026, 10, 2, 15, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )

        test_cases = [
            [answer_old, answer_middle, answer_new],
            [answer_old, answer_new, answer_middle],
            [answer_middle, answer_old, answer_new],
            [answer_middle, answer_new, answer_old],
            [answer_new, answer_middle, answer_old],
            [answer_new, answer_old, answer_middle],
        ]
        for answers in test_cases:
            with self.subTest():
                question = OpenKlant2Question(
                    url="http://example.com/question/1",
                    question="What is the final answer?",
                    question_kcm_uuid="q-uuid-1",
                    onderwerp="Philosophy",
                    kanaal="online",
                    taal="nld",
                    nummer="0001",
                    plaatsgevonden_op=datetime.datetime(
                        2024, 10, 2, 14, 0, 0, tzinfo=datetime.timezone.utc
                    ),
                    answers=answers,
                )

                self.assertEqual(question.answer, answer_new)
                self.assertEqual(question.answer.answer, "Final answer")
                self.assertEqual(question.answers[0], answer_new)
                self.assertEqual(question.answers[1], answer_middle)
                self.assertEqual(question.answers[2], answer_old)
                self.assertGreater(
                    question.answer.plaatsgevonden_op,
                    answer_middle.plaatsgevonden_op,
                )
                self.assertGreater(
                    question.answer.plaatsgevonden_op,
                    answer_old.plaatsgevonden_op,
                )

    def test_questions_for_partij_with_no_questions(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        with patch.object(service, "klantcontacten_for_partij", return_value=[]):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(questions, [])

    def test_questions_for_partij_question_without_answers(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        question_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "What was the question?",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-02T14:00:00Z",
            "url": "http://example.com/question/1",
            "gingOverOnderwerpobjecten": [],
        }

        with patch.object(
            service, "klantcontacten_for_partij", return_value=[question_kc]
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_kcm_uuid, "q-uuid-1")
        self.assertEqual(questions[0].question, "What was the question?")
        self.assertEqual(questions[0].answers, [])
        self.assertIsNone(questions[0].answer)

    def test_questions_for_partij_with_question_and_one_answer(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        # Question klantcontact
        question_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "What was the question?",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-02T14:00:00Z",
            "url": "http://example.com/question/1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q-uuid-1"}],
        }

        # Answer klantcontact
        answer_kc = {
            "uuid": "a-uuid-1",
            "inhoud": "42",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0002",
            "plaatsgevondenOp": "2024-10-02T15:00:00Z",
            "url": "http://example.com/answer/1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a-uuid-1"}],
        }

        # Onderwerp_object for question (wasKlantcontact is None/empty)
        question_oo = {
            "uuid": "oo-q-uuid-1",
            "klantcontact": {"uuid": "q-uuid-1"},
            "wasKlantcontact": None,
        }
        # Onderwerp_object for answer (wasKlantcontact points to question)
        answer_oo = {
            "uuid": "oo-a-uuid-1",
            "klantcontact": {"uuid": "a-uuid-1"},
            "wasKlantcontact": {"uuid": "q-uuid-1"},
        }

        # Mock the onderwerp_object.retrieve calls
        mock_client.onderwerp_object.retrieve.side_effect = [
            question_oo,  # First call for question
            answer_oo,  # Second call for answer
        ]

        with patch.object(
            service, "klantcontacten_for_partij", return_value=[question_kc, answer_kc]
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_kcm_uuid, "q-uuid-1")
        self.assertEqual(questions[0].question, "What was the question?")
        self.assertEqual(len(questions[0].answers), 1)
        self.assertEqual(questions[0].answer.answer, "42")
        self.assertEqual(questions[0].answer.answer_kcm_uuid, "a-uuid-1")

        # Verify onderwerp_object.retrieve was called correctly
        self.assertEqual(mock_client.onderwerp_object.retrieve.call_count, 2)
        mock_client.onderwerp_object.retrieve.assert_has_calls(
            [call("oo-q-uuid-1"), call("oo-a-uuid-1")]
        )

    def test_questions_for_partij_with_multiple_answers(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        question_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "What was the question?",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-02T14:00:00Z",
            "url": "http://example.com/question/1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q-uuid-1"}],
        }
        answer_old = {
            "uuid": "a-uuid-1",
            "inhoud": "First answer: 42",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0002",
            "plaatsgevondenOp": "2024-10-02T15:00:00Z",
            "url": "http://example.com/answer/1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a-uuid-1"}],
        }
        answer_middle = {
            "uuid": "a-uuid-2",
            "inhoud": "Updated answer: 43",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0003",
            "plaatsgevondenOp": "2024-10-02T16:00:00Z",
            "url": "http://example.com/answer/2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a-uuid-2"}],
        }
        answer_new = {
            "uuid": "a-uuid-3",
            "inhoud": "Final answer: 44",
            "onderwerp": "Philosophy",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0004",
            "plaatsgevondenOp": "2024-10-02T17:00:00Z",
            "url": "http://example.com/answer/3",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a-uuid-3"}],
        }

        # Onderwerp_objecten representing answers
        question_oo = {
            "uuid": "oo-q-uuid-1",
            "klantcontact": {"uuid": "q-uuid-1"},
            "wasKlantcontact": None,
        }
        answer_oo_old = {
            "uuid": "oo-a-uuid-1",
            "klantcontact": {"uuid": "a-uuid-1"},
            "wasKlantcontact": {"uuid": "q-uuid-1"},
        }
        answer_oo_middle = {
            "uuid": "oo-a-uuid-2",
            "klantcontact": {"uuid": "a-uuid-2"},
            "wasKlantcontact": {"uuid": "q-uuid-1"},
        }
        answer_oo_new = {
            "uuid": "oo-a-uuid-3",
            "klantcontact": {"uuid": "a-uuid-3"},
            "wasKlantcontact": {"uuid": "q-uuid-1"},
        }

        # Return klantcontacten in random order to test sorting
        mock_client.onderwerp_object.retrieve.side_effect = [
            answer_oo_middle,
            question_oo,
            answer_oo_new,
            answer_oo_old,
        ]

        with patch.object(
            service,
            "klantcontacten_for_partij",
            return_value=[answer_middle, question_kc, answer_new, answer_old],
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_kcm_uuid, "q-uuid-1")
        self.assertEqual(len(questions[0].answers), 3)

        # Verify answers are sorted newest first
        self.assertEqual(questions[0].answers[0].answer_kcm_uuid, "a-uuid-3")
        self.assertEqual(questions[0].answers[0].answer, "Final answer: 44")
        self.assertEqual(questions[0].answers[1].answer_kcm_uuid, "a-uuid-2")
        self.assertEqual(questions[0].answers[1].answer, "Updated answer: 43")
        self.assertEqual(questions[0].answers[2].answer_kcm_uuid, "a-uuid-1")
        self.assertEqual(questions[0].answers[2].answer, "First answer: 42")

        # Verify .answer property returns the newest
        self.assertEqual(questions[0].answer.answer_kcm_uuid, "a-uuid-3")
        self.assertEqual(questions[0].answer.answer, "Final answer: 44")

    def test_questions_for_partij_with_multiple_questions(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        # Question 1: no answers
        q1_kc = {
            "uuid": "q-uuid-1",
            "inhoud": "Question 1?",
            "onderwerp": "Topic 1",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-01T10:00:00Z",
            "url": "http://example.com/q1",
            "gingOverOnderwerpobjecten": [],
        }

        # Question 2: one answer
        q2_kc = {
            "uuid": "q-uuid-2",
            "inhoud": "Question 2?",
            "onderwerp": "Topic 2",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0002",
            "plaatsgevondenOp": "2024-10-02T10:00:00Z",
            "url": "http://example.com/q2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q2"}],
        }
        a2_kc = {
            "uuid": "a-uuid-2",
            "inhoud": "Answer to Q2",
            "onderwerp": "Topic 2",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0003",
            "plaatsgevondenOp": "2024-10-02T11:00:00Z",
            "url": "http://example.com/a2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a2"}],
        }

        # Question 3: two answers
        q3_kc = {
            "uuid": "q-uuid-3",
            "inhoud": "Question 3?",
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0004",
            "plaatsgevondenOp": "2024-10-03T10:00:00Z",
            "url": "http://example.com/q3",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-q3"}],
        }
        a3_1_kc = {
            "uuid": "a-uuid-3-1",
            "inhoud": "First answer to Q3",
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0005",
            "plaatsgevondenOp": "2024-10-03T11:00:00Z",
            "url": "http://example.com/a3-1",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a3-1"}],
        }
        a3_2_kc = {
            "uuid": "a-uuid-3-2",
            "inhoud": "Second answer to Q3",
            "onderwerp": "Topic 3",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0006",
            "plaatsgevondenOp": "2024-10-03T12:00:00Z",
            "url": "http://example.com/a3-2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a3-2"}],
        }

        # Onderwerp_objecten representing answers
        q2_oo = {"uuid": "oo-q2", "wasKlantcontact": None}
        a2_oo = {"uuid": "oo-a2", "wasKlantcontact": {"uuid": "q-uuid-2"}}
        q3_oo = {"uuid": "oo-q3", "wasKlantcontact": None}
        a3_1_oo = {"uuid": "oo-a3-1", "wasKlantcontact": {"uuid": "q-uuid-3"}}
        a3_2_oo = {"uuid": "oo-a3-2", "wasKlantcontact": {"uuid": "q-uuid-3"}}

        mock_client.onderwerp_object.retrieve.side_effect = [
            q2_oo,
            a2_oo,
            q3_oo,
            a3_1_oo,
            a3_2_oo,
        ]

        with patch.object(
            service,
            "klantcontacten_for_partij",
            return_value=[q1_kc, q2_kc, a2_kc, q3_kc, a3_1_kc, a3_2_kc],
        ):
            questions = service.questions_for_partij("partij-uuid")

        self.assertEqual(len(questions), 3)

        q1 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-1")
        q2 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-2")
        q3 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-3")

        # Q1: no answers
        self.assertEqual(q1.question, "Question 1?")
        self.assertEqual(len(q1.answers), 0)
        self.assertIsNone(q1.answer)

        # Q2: one answer
        self.assertEqual(q2.question, "Question 2?")
        self.assertEqual(len(q2.answers), 1)
        self.assertEqual(q2.answer.answer, "Answer to Q2")

        # Q3: two answers (sorted newest first)
        self.assertEqual(q3.question, "Question 3?")
        self.assertEqual(len(q3.answers), 2)
        self.assertEqual(q3.answers[0].answer, "Second answer to Q3")
        self.assertEqual(q3.answers[1].answer, "First answer to Q3")
        self.assertEqual(q3.answer.answer, "Second answer to Q3")
