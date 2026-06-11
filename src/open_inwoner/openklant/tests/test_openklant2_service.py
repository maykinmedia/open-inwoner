import datetime
from unittest.mock import Mock, call, patch

from django.test import TestCase

from openklant_client.exceptions import NotFound as OK2NotFound

from open_inwoner.accounts.choices import DigitalAddressType
from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.openklant.models import DigitaalAdresKlant2Mapping
from open_inwoner.openklant.services import (
    OpenKlant2Answer,
    OpenKlant2Question,
    OpenKlant2Service,
    _normalize_email,
    _normalize_phone,
)
from open_inwoner.openklant.tests.factories import (
    DigitaalAdresKlant2MappingFactory,
    OpenKlant2ConfigFactory,
)


@patch("open_inwoner.openklant.services.OpenKlantClient")
class UpdateUserFromPartijTestCase(TestCase):
    PARTIJ_UUID = "00000000-0000-0000-0001-000000000001"
    EMAIL_UUID = "00000000-0000-0000-0001-000000000002"
    PHONE1_UUID = "00000000-0000-0000-0001-000000000003"
    PHONE2_UUID = "00000000-0000-0000-0001-000000000004"
    PHONE3_UUID = "00000000-0000-0000-0001-000000000005"
    VOORKEURS_UUID = "00000000-0000-0000-0001-000000000006"

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def _setup_mock(self, mock_client_class, adressen, voorkeurs_uuid=None):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = {
            "count": len(adressen),
            "next": None,
            "previous": None,
            "results": adressen,
        }
        mock_client.partij.retrieve.return_value = {
            "voorkeursDigitaalAdres": (
                {"uuid": voorkeurs_uuid} if voorkeurs_uuid else None
            ),
        }
        return mock_client

    def _make_adres(self, uuid, soort, adres, is_standaard=False):
        return {
            "uuid": uuid,
            "soortDigitaalAdres": soort,
            "adres": adres,
            "isStandaardAdres": is_standaard,
            "omschrijving": "",
            "verstrektDoorPartij": {"uuid": self.PARTIJ_UUID},
            "verstrektDoorBetrokkene": None,
        }

    def test_email_not_updated_when_already_exists_for_another_user(
        self, mock_client_class
    ):
        UserFactory(email="taken@example.com")
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.EMAIL_UUID, "email", "taken@example.com", is_standaard=True
                ),
            ],
        )

        user = UserFactory(email="original@example.com")
        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        user.refresh_from_db()
        self.assertEqual(user.email, "original@example.com")

    def test_email_updated_when_available(self, mock_client_class):
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.EMAIL_UUID, "email", "available@example.com", is_standaard=True
                ),
            ],
        )

        user = UserFactory(email="old@example.com")
        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        user.refresh_from_db()
        self.assertEqual(user.email, "available@example.com")

    def test_primary_phone_maps_to_user_phonenumber(self, mock_client_class):
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.PHONE1_UUID, "telefoonnummer", "0612345678", is_standaard=True
                ),
                self._make_adres(
                    self.PHONE2_UUID, "telefoonnummer", "0687654321", is_standaard=False
                ),
            ],
        )

        user = UserFactory(phonenumber="")
        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        user.refresh_from_db()
        self.assertEqual(user.phonenumber, "0612345678")

    def test_non_primary_phone_created_as_digital_address(self, mock_client_class):
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.PHONE1_UUID, "telefoonnummer", "0612345678", is_standaard=True
                ),
                self._make_adres(
                    self.PHONE2_UUID, "telefoonnummer", "0687654321", is_standaard=False
                ),
            ],
        )

        user = UserFactory(phonenumber="")
        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        secondary = user.digital_addresses.filter(
            type=DigitalAddressType.phone, value="0687654321"
        )
        self.assertTrue(secondary.exists())

    def test_logs_warning_when_more_than_two_phone_numbers(self, mock_client_class):
        phone_uuids = [self.PHONE1_UUID, self.PHONE2_UUID, self.PHONE3_UUID]
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    phone_uuids[i],
                    "telefoonnummer",
                    f"061234567{i}",
                    is_standaard=(i == 0),
                )
                for i in range(3)
            ],
        )

        user = UserFactory()
        with self.assertLogs(
            "open_inwoner.openklant.services", level="WARNING"
        ) as logs:
            OpenKlant2Service(config=self.config).update_user_from_partij(
                self.PARTIJ_UUID, user
            )

        self.assertTrue(
            any("More than two phone numbers found" in log for log in logs.output)
        )

    def test_non_primary_phone_without_primary_does_not_set_phonenumber(
        self, mock_client_class
    ):
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.PHONE1_UUID, "telefoonnummer", "0612345678", is_standaard=False
                ),
            ],
        )

        user = UserFactory(phonenumber="")
        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        user.refresh_from_db()
        self.assertEqual(user.phonenumber, "")

    def test_known_uuid_updates_local_value_via_mapping(self, mock_client_class):
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.EMAIL_UUID, "email", "new@example.com", is_standaard=True
                ),
            ],
        )

        user = UserFactory(email="old@example.com")
        email_addr = user.digital_addresses.get(type="email")
        DigitaalAdresKlant2MappingFactory(
            digital_address=email_addr, ok2_uuid=self.EMAIL_UUID
        )

        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        email_addr.refresh_from_db()
        self.assertEqual(email_addr.value, "new@example.com")

    def test_unknown_uuid_creates_new_digital_address_and_mapping(
        self, mock_client_class
    ):
        from open_inwoner.accounts.choices import DigitalAddressType

        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.EMAIL_UUID, "email", "old@example.com", is_standaard=True
                ),
                self._make_adres(
                    self.PHONE1_UUID, "telefoonnummer", "0612345678", is_standaard=True
                ),
            ],
        )

        user = UserFactory(email="old@example.com", phonenumber="")
        # No mappings exist yet

        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        self.assertTrue(
            DigitaalAdresKlant2Mapping.objects.filter(
                digital_address__user=user,
                ok2_uuid=self.PHONE1_UUID,
            ).exists()
        )
        self.assertTrue(
            user.digital_addresses.filter(
                type=DigitalAddressType.phone, value="0612345678"
            ).exists()
        )

    def test_stale_local_address_deleted_when_absent_from_remote(
        self, mock_client_class
    ):
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.EMAIL_UUID, "email", "test@example.com", is_standaard=True
                ),
            ],
        )

        user = UserFactory(email="test@example.com", phonenumber="0612345678")
        phone_addr = user.digital_addresses.get(type="phone")
        DigitaalAdresKlant2MappingFactory(
            digital_address=phone_addr, ok2_uuid=self.PHONE1_UUID
        )
        email_addr = user.digital_addresses.get(type="email")
        DigitaalAdresKlant2MappingFactory(
            digital_address=email_addr, ok2_uuid=self.EMAIL_UUID
        )

        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        self.assertFalse(user.digital_addresses.filter(type="phone").exists())

    def test_voorkeurs_digitaal_adres_sets_preferred_address(self, mock_client_class):
        # EMAIL_UUID is used for both the email address and voorkeursDigitaalAdres
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.EMAIL_UUID, "email", "test@example.com", is_standaard=True
                ),
            ],
            voorkeurs_uuid=self.EMAIL_UUID,
        )

        user = UserFactory(email="test@example.com", phonenumber="")
        email_addr = user.digital_addresses.get(type="email")
        DigitaalAdresKlant2MappingFactory(
            digital_address=email_addr, ok2_uuid=self.EMAIL_UUID
        )

        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        user.refresh_from_db()
        self.assertEqual(user.preferred_address, email_addr)

    def test_voorkeurs_digitaal_adres_skipped_when_no_mapping(self, mock_client_class):
        self._setup_mock(
            mock_client_class,
            [
                self._make_adres(
                    self.EMAIL_UUID, "email", "test@example.com", is_standaard=True
                ),
            ],
            voorkeurs_uuid=self.VOORKEURS_UUID,
        )

        user = UserFactory(email="test@example.com", phonenumber="")
        # No mapping for VOORKEURS_UUID

        OpenKlant2Service(config=self.config).update_user_from_partij(
            self.PARTIJ_UUID, user
        )

        user.refresh_from_db()
        self.assertIsNone(user.preferred_address)


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

    def test_questions_for_partij_missing_inhoud(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = OpenKlant2Service(config=self.config)

        # Question 1: question misses inhoud
        q1_kc = {
            "uuid": "q-uuid-1",
            "inhoud": None,
            "onderwerp": "Topic 1",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0001",
            "plaatsgevondenOp": "2024-10-01T10:00:00Z",
            "url": "http://example.com/q1",
            "gingOverOnderwerpobjecten": [],
        }

        # Question 2: one answer with missing inhoud
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
            "inhoud": None,
            "onderwerp": "Topic 2",
            "kanaal": "oip_mijn_vragen",
            "taal": "nld",
            "nummer": "0003",
            "plaatsgevondenOp": "2024-10-02T11:00:00Z",
            "url": "http://example.com/a2",
            "gingOverOnderwerpobjecten": [{"uuid": "oo-a2"}],
        }

        # Question 3: two answers, one with and one without inhoud
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
            "inhoud": None,
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

        self.assertEqual(len(questions), 2)

        # q1 (inhoud=None) is skipped entirely
        self.assertFalse(any(q.question_kcm_uuid == "q-uuid-1" for q in questions))

        # q2 is present but its answer (inhoud=None) is skipped
        q2 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-2")
        self.assertEqual(q2.question, "Question 2?")
        self.assertEqual(len(q2.answers), 0)

        # q3 is present; a3_1 (inhoud=None) is skipped, a3_2 survives
        q3 = next(q for q in questions if q.question_kcm_uuid == "q-uuid-3")
        self.assertEqual(q3.question, "Question 3?")
        self.assertEqual(len(q3.answers), 1)
        self.assertEqual(q3.answers[0].answer, "Second answer to Q3")


class NormalizeHelpersTestCase(TestCase):
    def test_normalize(self):
        cases = [
            (_normalize_phone, "06-12 345 678", "0612345678"),
            (_normalize_phone, "+31 6 12 34 56 78", "0031612345678"),
            (_normalize_phone, "  0612345678  ", "0612345678"),
            (_normalize_email, "User@Example.COM", "user@example.com"),
            (_normalize_email, "  user@example.com  ", "user@example.com"),
        ]
        for fn, value, expected in cases:
            with self.subTest(fn=fn.__name__, value=value):
                self.assertEqual(fn(value), expected, f"{fn.__name__}({value!r})")


def _make_digitaal_adres(adres, soort, is_standaard=True, uuid_str="addr-uuid"):
    return {
        "uuid": uuid_str,
        "soortDigitaalAdres": soort,
        "adres": adres,
        "isStandaardAdres": is_standaard,
        "omschrijving": "OIP profiel",
        "verstrektDoorPartij": {"uuid": "partij-uuid"},
        "verstrektDoorBetrokkene": None,
    }


@patch("open_inwoner.openklant.services.OpenKlantClient")
class GetOrCreateDigitaalAdresNormalizationTestCase(TestCase):
    """Deduplication must survive formatting differences in stored vs incoming values."""

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def _service_with_existing(self, mock_client_class, existing_adres):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [existing_adres],
        }
        return OpenKlant2Service(config=self.config), mock_client

    def test_phone_not_duplicated_when_formatting_differs(self, mock_client_class):
        existing = _make_digitaal_adres("06-12 345 678", "telefoonnummer")
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0612345678",
            is_standaard_adres=True,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()

    def test_phone_not_duplicated_when_international_format_differs(
        self, mock_client_class
    ):
        existing = _make_digitaal_adres("+31 6 12345678", "telefoonnummer")
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="+31612345678",
            is_standaard_adres=True,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()

    def test_email_not_duplicated_when_case_differs(self, mock_client_class):
        existing = _make_digitaal_adres("User@Example.COM", "email", is_standaard=False)
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="email",
            adres="user@example.com",
            is_standaard_adres=False,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()

    def test_phone_created_normalized_when_no_existing(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = {
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        }
        mock_client.digitaal_adres.create.return_value = _make_digitaal_adres(
            "0612345678", "telefoonnummer"
        )

        service = OpenKlant2Service(config=self.config)
        service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="06-12 345 678",
            is_standaard_adres=True,
        )

        create_call = mock_client.digitaal_adres.create.call_args
        self.assertEqual(create_call[1]["data"]["adres"], "0612345678")

    def test_email_created_normalized_when_no_existing(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = {
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        }
        mock_client.digitaal_adres.create.return_value = _make_digitaal_adres(
            "user@example.com", "email", is_standaard=False
        )

        service = OpenKlant2Service(config=self.config)
        service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="email",
            adres="  User@Example.COM  ",
            is_standaard_adres=False,
        )

        create_call = mock_client.digitaal_adres.create.call_args
        self.assertEqual(create_call[1]["data"]["adres"], "user@example.com")

    def test_different_phone_still_creates_new(self, mock_client_class):
        existing = _make_digitaal_adres("0612345678", "telefoonnummer")
        service, mock_client = self._service_with_existing(mock_client_class, existing)
        mock_client.digitaal_adres.create.return_value = _make_digitaal_adres(
            "0687654321", "telefoonnummer", uuid_str="new-uuid"
        )

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0687654321",
            is_standaard_adres=True,
        )

        self.assertTrue(created)
        mock_client.digitaal_adres.create.assert_called_once()

    def test_not_duplicated_when_only_is_standaard_differs(self, mock_client_class):
        existing = _make_digitaal_adres(
            "0612345678", "telefoonnummer", is_standaard=True
        )
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0612345678",
            is_standaard_adres=False,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()
        mock_client.digitaal_adres.partial_update.assert_not_called()

    def test_not_duplicated_when_is_standaard_adres_is_none(self, mock_client_class):
        existing = _make_digitaal_adres(
            "0612345678", "telefoonnummer", is_standaard=True
        )
        service, mock_client = self._service_with_existing(mock_client_class, existing)

        _, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0612345678",
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()
        mock_client.digitaal_adres.partial_update.assert_not_called()

    def test_patches_is_standaard_when_existing_is_not_standaard(
        self, mock_client_class
    ):
        existing = _make_digitaal_adres(
            "0612345678", "telefoonnummer", is_standaard=False
        )
        service, mock_client = self._service_with_existing(mock_client_class, existing)
        patched = _make_digitaal_adres(
            "0612345678", "telefoonnummer", is_standaard=True
        )
        mock_client.digitaal_adres.partial_update.return_value = patched

        result, created = service.get_or_create_digitaal_adres_for_partij(
            partij_uuid="partij-uuid",
            soort_adres="telefoonnummer",
            adres="0612345678",
            is_standaard_adres=True,
        )

        self.assertFalse(created)
        mock_client.digitaal_adres.create.assert_not_called()
        mock_client.digitaal_adres.partial_update.assert_called_once_with(
            "addr-uuid", data={"isStandaardAdres": True}
        )
        self.assertEqual(result, patched)


@patch("open_inwoner.openklant.services.OpenKlantClient")
class UpdatePartijFromUserDataTestCase(TestCase):
    PARTIJ_UUID = "00000000-0000-0000-0000-000000000001"
    EMAIL_REMOTE_UUID = "00000000-0000-0000-0000-000000000002"
    PHONE_REMOTE_UUID = "00000000-0000-0000-0000-000000000003"
    EXISTING_REMOTE_UUID = "00000000-0000-0000-0000-000000000004"
    KNOWN_MAPPING_UUID = "00000000-0000-0000-0000-000000000005"
    STALE_MAPPING_UUID = "00000000-0000-0000-0000-000000000006"
    NEW_REMOTE_UUID = "00000000-0000-0000-0000-000000000007"

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def _make_adres(self, uuid, soort, adres, is_standaard=False):
        return {
            "uuid": uuid,
            "soortDigitaalAdres": soort,
            "adres": adres,
            "isStandaardAdres": is_standaard,
            "omschrijving": "OIP profiel",
            "verstrektDoorPartij": {"uuid": self.PARTIJ_UUID},
            "verstrektDoorBetrokkene": None,
        }

    def _list_response(self, results):
        return {
            "count": len(results),
            "next": None,
            "previous": None,
            "results": results,
        }

    def test_creates_email_address_for_new_user(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            self.EMAIL_REMOTE_UUID, "email", "new@example.com", is_standaard=True
        )
        user = UserFactory(email="new@example.com", phonenumber="")

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        self.assertEqual(result, ["digitaleAddresen.email"])
        create_data = mock_client.digitaal_adres.create.call_args[1]["data"]
        self.assertTrue(create_data["isStandaardAdres"])
        self.assertEqual(create_data["soortDigitaalAdres"], "email")

    def test_creates_phone_as_standaard_adres(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.side_effect = [
            self._make_adres(
                self.EMAIL_REMOTE_UUID, "email", "test@example.com", is_standaard=True
            ),
            self._make_adres(
                self.PHONE_REMOTE_UUID,
                "telefoonnummer",
                "0612345678",
                is_standaard=True,
            ),
        ]
        user = UserFactory(email="test@example.com", phonenumber="0612345678")

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        calls = mock_client.digitaal_adres.create.call_args_list
        phone_call = next(
            c for c in calls if c[1]["data"]["soortDigitaalAdres"] == "telefoonnummer"
        )
        self.assertTrue(phone_call[1]["data"]["isStandaardAdres"])

    def test_fetches_remote_adressen_exactly_once_for_multiple_addresses(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.side_effect = [
            self._make_adres(
                self.EMAIL_REMOTE_UUID, "email", "test@example.com", is_standaard=True
            ),
            self._make_adres(
                self.PHONE_REMOTE_UUID,
                "telefoonnummer",
                "0612345678",
                is_standaard=True,
            ),
        ]
        user = UserFactory(email="test@example.com", phonenumber="0612345678")

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mock_client.digitaal_adres.list.assert_called_once_with(
            params={"verstrektDoorPartij__uuid": self.PARTIJ_UUID}
        )

    def test_reuses_existing_remote_adres_via_value_match(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        existing = self._make_adres(
            self.EXISTING_REMOTE_UUID, "email", "test@example.com", is_standaard=True
        )
        mock_client.digitaal_adres.list.return_value = self._list_response([existing])
        user = UserFactory(email="test@example.com", phonenumber="")

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        self.assertEqual(result, [])
        mock_client.digitaal_adres.create.assert_not_called()

    def test_reuse_stores_mapping_for_future_uuid_based_sync(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        existing = self._make_adres(
            self.EXISTING_REMOTE_UUID, "email", "test@example.com", is_standaard=True
        )
        mock_client.digitaal_adres.list.return_value = self._list_response([existing])
        user = UserFactory(email="test@example.com", phonenumber="")
        email_addr = user.digital_addresses.get(type="email")

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mapping = DigitaalAdresKlant2Mapping.objects.get(digital_address=email_addr)
        self.assertEqual(str(mapping.ok2_uuid), self.EXISTING_REMOTE_UUID)

    def test_patch_via_uuid_when_mapping_exists(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        user = UserFactory(email="test@example.com", phonenumber="")
        email_addr = user.digital_addresses.get(type="email")
        DigitaalAdresKlant2MappingFactory(
            digital_address=email_addr, ok2_uuid=self.KNOWN_MAPPING_UUID
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mock_client.digitaal_adres.partial_update.assert_called_once_with(
            self.KNOWN_MAPPING_UUID,
            data={"adres": "test@example.com", "isStandaardAdres": True},
        )
        mock_client.digitaal_adres.create.assert_not_called()
        self.assertEqual(result, [])

    def test_self_heals_on_404_from_patch(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.partial_update.side_effect = OK2NotFound(
            response=Mock(status_code=404),
            body={
                "type": "",
                "code": "not_found",
                "title": "Not found",
                "status": 404,
                "detail": "",
                "instance": "",
            },
        )
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            self.NEW_REMOTE_UUID, "email", "test@example.com", is_standaard=True
        )
        user = UserFactory(email="test@example.com", phonenumber="")
        email_addr = user.digital_addresses.get(type="email")
        DigitaalAdresKlant2MappingFactory(
            digital_address=email_addr, ok2_uuid=self.STALE_MAPPING_UUID
        )

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mock_client.digitaal_adres.create.assert_called_once()
        self.assertEqual(result, ["digitaleAddresen.email"])

    def test_no_remote_fetch_when_all_addresses_have_mappings(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        user = UserFactory(email="test@example.com", phonenumber="")
        email_addr = user.digital_addresses.get(type="email")
        DigitaalAdresKlant2MappingFactory(
            digital_address=email_addr, ok2_uuid=self.KNOWN_MAPPING_UUID
        )

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mock_client.digitaal_adres.list.assert_not_called()

    def test_syncs_voorkeurs_digitaal_adres_when_mapping_exists(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        user = UserFactory(email="test@example.com", phonenumber="")
        email_addr = user.digital_addresses.get(type="email")
        DigitaalAdresKlant2MappingFactory(
            digital_address=email_addr, ok2_uuid=self.KNOWN_MAPPING_UUID
        )
        user.preferred_address = email_addr
        user.save()

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mock_client.partij.partial_update.assert_called_once_with(
            self.PARTIJ_UUID,
            data={"voorkeursDigitaalAdres": {"uuid": self.KNOWN_MAPPING_UUID}},
        )
        self.assertIn("voorkeursDigitaalAdres", result)

    def test_syncs_voorkeurs_digitaal_adres_when_mapping_created_in_same_call(
        self, mock_client_class
    ):
        """
        When the preferred address has no pre-existing mapping, the address sync
        loop creates one. The voorkeursDigitaalAdres sync then finds it and patches.
        """
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.digitaal_adres.list.return_value = self._list_response([])
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            self.EMAIL_REMOTE_UUID, "email", "test@example.com", is_standaard=True
        )
        user = UserFactory(email="test@example.com", phonenumber="")
        email_addr = user.digital_addresses.get(type="email")
        user.preferred_address = email_addr
        user.save()

        service = OpenKlant2Service(config=self.config)
        result = service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mock_client.partij.partial_update.assert_called_once_with(
            self.PARTIJ_UUID,
            data={"voorkeursDigitaalAdres": {"uuid": self.EMAIL_REMOTE_UUID}},
        )
        self.assertIn("voorkeursDigitaalAdres", result)

    def test_no_voorkeurs_sync_when_preferred_address_is_null(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        user = UserFactory(email="test@example.com", phonenumber="")
        email_addr = user.digital_addresses.get(type="email")
        DigitaalAdresKlant2MappingFactory(
            digital_address=email_addr, ok2_uuid=self.KNOWN_MAPPING_UUID
        )
        # preferred_address is null (default)

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mock_client.partij.partial_update.assert_not_called()

    def test_deletes_orphaned_remote_adres_after_value_change(self, mock_client_class):
        """
        When a local address value changed (e.g. old email → new email) and no mapping
        exists yet, the backfill creates a new remote adres for the new value. The old
        remote adres (with the old value) has no local counterpart and must be deleted.
        """
        ORPHAN_UUID = "00000000-0000-0000-0002-000000000001"
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        orphan_adres = self._make_adres(
            ORPHAN_UUID, "email", "old@example.com", is_standaard=True
        )
        mock_client.digitaal_adres.list.return_value = self._list_response(
            [orphan_adres]
        )
        mock_client.digitaal_adres.create.return_value = self._make_adres(
            self.EMAIL_REMOTE_UUID, "email", "new@example.com", is_standaard=True
        )
        user = UserFactory(email="new@example.com", phonenumber="")
        # No mapping — first sync after email changed from "old" to "new"

        service = OpenKlant2Service(config=self.config)
        service.update_partij_from_user_data(
            partij_uuid=self.PARTIJ_UUID,
            user=user,
        )

        mock_client.digitaal_adres.create.assert_called_once()
        mock_client.digitaal_adres.delete.assert_called_once_with(ORPHAN_UUID)


@patch("open_inwoner.openklant.services.OpenKlantClient")
class KlantcontactenForPartijTestCase(TestCase):
    PARTIJ_UUID = "partij-uuid-1234"

    def setUp(self):
        self.config = OpenKlant2ConfigFactory()

    def _make_kc(self, uuid, partij_uuid=None, initiator=True, expand_key="_expand"):
        betrokkene = {"initiator": initiator}
        if partij_uuid is not None:
            betrokkene["wasPartij"] = {"uuid": partij_uuid}
        else:
            betrokkene["wasPartij"] = None
        return {
            "uuid": uuid,
            expand_key: {"hadBetrokkenen": [betrokkene]},
        }

    def test_matching_klantcontact_is_returned(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = self._make_kc("kc-1", partij_uuid=self.PARTIJ_UUID, initiator=True)
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [kc])

    def test_different_partij_uuid_is_excluded(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = self._make_kc("kc-1", partij_uuid="other-partij-uuid", initiator=True)
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_non_initiator_is_excluded(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = self._make_kc("kc-1", partij_uuid=self.PARTIJ_UUID, initiator=False)
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_missing_expand_key_is_excluded_without_exception(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = {"uuid": "kc-bad"}  # no _expand key at all
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_missing_had_betrokkenen_in_expand_is_excluded_without_exception(
        self, mock_client_class
    ):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        kc = {"uuid": "kc-bad", "_expand": {}}  # hadBetrokkenen absent
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_null_was_partij_is_excluded_without_exception(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        # wasPartij is null — the betrokkene belongs to no partij
        kc = self._make_kc("kc-1", partij_uuid=None, initiator=True)
        mock_client.klant_contact.list_iter.return_value = iter([kc])

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [])

    def test_malformed_items_excluded_valid_items_returned(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        good = self._make_kc("kc-good", partij_uuid=self.PARTIJ_UUID, initiator=True)
        bad_no_expand = {"uuid": "kc-bad-1"}
        bad_empty_expand = {"uuid": "kc-bad-2", "_expand": {}}
        mock_client.klant_contact.list_iter.return_value = iter(
            [bad_no_expand, bad_empty_expand, good]
        )

        service = OpenKlant2Service(config=self.config)
        result = list(service.klantcontacten_for_partij(self.PARTIJ_UUID))

        self.assertEqual(result, [good])
