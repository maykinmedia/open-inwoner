import threading
from datetime import datetime
from unittest.mock import patch

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext

import requests_mock

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.clients import (
    build_contactmomenten_client,
    build_klanten_client,
)
from open_inwoner.openklant.constants import KlantenServiceType, Status
from open_inwoner.openklant.models import ContactFormSubject, ESuiteKlantConfig
from open_inwoner.openklant.services import (
    KlantContactMomentSkipReason,
    eSuiteVragenService,
)
from open_inwoner.openklant.tests.data import CONTACTMOMENTEN_ROOT, MockAPIReadData
from open_inwoner.utils.url import uuid_from_url


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class eSuiteVragenServiceTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        MockAPIReadData.setUpServices()
        self.service = eSuiteVragenService()
        self.user = UserFactory()
        klanten_config = ESuiteKlantConfig.get_solo()
        klanten_config.exclude_contactmoment_kanalen = ["intern_initiatief"]
        klanten_config.save()

        self.contactformsubject = ContactFormSubject.objects.create(
            subject="oip_subject",
            esuite_subject_code="e_suite_subject_code",
            esuite_config=klanten_config,
        )

    def test_list_questions_returns_expected_rows(self, m):
        data = MockAPIReadData().install_mocks(m)
        config = ESuiteKlantConfig.get_solo()

        for user, params, expected_klantcontact, expected_contactmoment, use_rsin in (
            (
                data.user,
                {"user_bsn": "100000001"},
                data.klant_contactmoment,
                data.contactmoment,
                False,
            ),
            (
                data.eherkenning_user,
                {"user_kvk_or_rsin": "12345678"},
                data.klant_contactmoment2,
                data.contactmoment2,
                False,
            ),
            (
                data.eherkenning_user,
                {"user_kvk_or_rsin": "12345678", "vestigingsnummer": "1234"},
                data.klant_contactmoment4,
                data.contactmoment_vestiging,
                False,
            ),
            (
                data.eherkenning_user,
                # RSIN case
                {"user_kvk_or_rsin": "000000000", "vestigingsnummer": "1234"},
                data.klant_contactmoment4,
                data.contactmoment_vestiging,
                True,
            ),
            (
                data.eherkenning_user,
                # RSIN case
                {"user_kvk_or_rsin": "000000000"},
                data.klant_contactmoment2,
                data.contactmoment2,
                True,
            ),
        ):
            with self.subTest(f"{user=} {params=} {use_rsin=}"):
                config.use_rsin_for_innNnpId_query_parameter = use_rsin
                config.save()

                questions = self.service.list_questions(params, user).questions

                self.assertEqual(len(questions), 1)
                self.assertEqual(
                    questions[0],
                    {
                        "identification": expected_contactmoment["identificatie"],
                        "api_source_url": expected_contactmoment["url"],
                        "api_source_uuid": uuid_from_url(expected_contactmoment["url"]),
                        "subject": self.contactformsubject.subject,
                        "question_text": expected_contactmoment["tekst"],
                        "answer_text": expected_contactmoment["antwoord"],
                        "registered_date": datetime.fromisoformat(
                            expected_contactmoment["registratiedatum"]
                        ),
                        "status": Status.afgehandeld.label,
                        "channel": expected_contactmoment["kanaal"],
                        "new_answer_available": False,
                        "api_service": KlantenServiceType.ESUITE,
                    },
                )
                m.reset_mock()

    def test_list_questions_resolves_per_page_lookups_once(self, m):
        """The per-page lookups must not be resolved once per contactmoment.

        Asserting per table rather than a total: the total also covers config reads
        that do not scale with the number of contactmomenten, which would make this
        brittle without saying anything about the behaviour under test.

        The kanaal exclusion is lifted so both mocked contactmomenten reach
        `_build_question_dto`, which is where the per-row queries used to happen.
        """
        klanten_config = ESuiteKlantConfig.get_solo()
        klanten_config.exclude_contactmoment_kanalen = []
        klanten_config.save()

        data = MockAPIReadData().install_mocks(m)

        with CaptureQueriesContext(connection) as captured:
            result = self.service.list_questions({"user_bsn": data.user.bsn}, data.user)

        self.assertEqual(len(result.questions), 2)

        def queries_touching(table: str) -> list[str]:
            return [q["sql"] for q in captured.captured_queries if table in q["sql"]]

        self.assertEqual(
            len(queries_touching("openklant_contactformsubject")),
            1,
            msg="subject mapping should be resolved once for the whole page",
        )
        # One SELECT to find existing rows, one INSERT, one SELECT to read them back.
        self.assertEqual(
            len(queries_touching("openklant_klantcontactmomentanswer")),
            3,
            msg="answer mapping should be resolved once for the whole page",
        )

    def test_subject_mapping_prefers_the_first_subject_for_a_code(self, m):
        """Several OIP subjects may share one e-suite code; the first by order wins."""
        data = MockAPIReadData().install_mocks(m)
        ContactFormSubject.objects.create(
            subject="duplicate_subject",
            esuite_subject_code=self.contactformsubject.esuite_subject_code,
            esuite_config=ESuiteKlantConfig.get_solo(),
        )
        # A subject for an unrelated code, ordered first, must not be picked up.
        unrelated = ContactFormSubject.objects.create(
            subject="unrelated_subject",
            esuite_subject_code="some_other_code",
            esuite_config=ESuiteKlantConfig.get_solo(),
        )
        unrelated.top()

        result = self.service.list_questions({"user_bsn": data.user.bsn}, data.user)

        self.assertEqual(
            result.questions[0]["subject"], self.contactformsubject.subject
        )

    def test_unresolvable_contactmoment_is_reported_as_skipped(self, m):
        """A contactmoment that cannot be retrieved must not cost the whole page."""
        data = MockAPIReadData().install_mocks(m)
        # Registered last, so it takes precedence over the mock install_mocks set up.
        m.get(data.contactmoment_intern["url"], status_code=500)

        result = self.service.fetch_klantcontactmomenten(user_bsn=data.user.bsn)

        self.assertEqual(len(result.klantcontactmomenten), 1)
        self.assertEqual(
            str(result.klantcontactmomenten[0].uuid), data.klant_contactmoment["uuid"]
        )
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.skipped[0].kcm_url, data.contactmoment_intern["url"])
        self.assertEqual(
            result.skipped[0].reason,
            KlantContactMomentSkipReason.RESOLUTION_FAILED,
        )
        self.assertTrue(result.is_incomplete)

    def test_incompleteness_propagates_to_list_questions(self, m):
        data = MockAPIReadData().install_mocks(m)
        m.get(data.contactmoment_intern["url"], status_code=500)

        result = self.service.list_questions({"user_bsn": data.user.bsn}, data.user)

        # The intern contactmoment is excluded by kanaal anyway, so the question list
        # is unchanged; the point is that the failure is still reported.
        self.assertEqual(len(result.questions), 1)
        self.assertTrue(result.is_incomplete)

    def test_resolution_stops_at_the_deadline(self, m):
        """An exhausted time budget leaves the rest unresolved rather than hanging.

        Blocks the resolve call with a threading.Event rather than relying on a
        tiny timeout racing real (mocked, near-instant) HTTP calls: with those,
        whether as_completed(timeout=0) sees anything as "already done" depends on
        thread scheduling, not the code under test. A timer releases the block so
        the still-pending futures can complete once `parallel`'s `__exit__` waits
        for them, instead of hanging the test.

        The release must not fire until *after* as_completed's initial "already
        finished" snapshot, or the (still-unresolved) kcm looks like a clean
        success instead of a timeout. Submitting the futures does real work
        (building a client per kcm), so a short margin here raced that submission
        under CI load and was flaky; this margin is generous on purpose.
        """
        data = MockAPIReadData().install_mocks(m)
        config = ESuiteKlantConfig.get_solo()
        config.contactmoment_fetch_timeout = 0
        config.save()

        release = threading.Event()
        timer = threading.Timer(1, release.set)

        def _blocking_resolve(kcm, client):
            release.wait(timeout=10)

        with patch.object(
            eSuiteVragenService,
            "_resolve_single_contactmoment",
            side_effect=_blocking_resolve,
        ):
            timer.start()
            try:
                result = eSuiteVragenService().fetch_klantcontactmomenten(
                    user_bsn=data.user.bsn
                )
            finally:
                release.set()
                timer.cancel()

        self.assertEqual(result.klantcontactmomenten, [])
        self.assertEqual(len(result.skipped), 2)
        self.assertEqual(
            {skipped.reason for skipped in result.skipped},
            {KlantContactMomentSkipReason.TIMEOUT},
        )
        self.assertTrue(result.is_incomplete)

    def test_listing_klantcontactmomenten_does_not_resolve_contactmomenten(self, m):
        """The client lists; fanning the resolution out is the service's job."""
        data = MockAPIReadData().install_mocks(m)
        klant = build_klanten_client().retrieve_klant(user_bsn=data.user.bsn)
        m.reset_mock()

        kcms = build_contactmomenten_client().list_klantcontactmomenten_for_klant(klant)

        self.assertEqual(len(kcms), 2)
        for kcm in kcms:
            self.assertIsInstance(kcm.contactmoment, str)
        self.assertEqual(len(m.request_history), 1)

    def test_fetch_klantcontactmoment_resolves_only_the_matching_contactmoment(self, m):
        """The detail page must not pay for resolving every klantcontactmoment.

        `data.user` has two klantcontactmomenten (`klant_contactmoment` and the
        interne one); only the requested one's contactmoment should be retrieved.
        """
        data = MockAPIReadData().install_mocks(m)

        kcm = self.service.fetch_klantcontactmoment(
            data.klant_contactmoment["uuid"], user_bsn=data.user.bsn
        )

        self.assertIsNotNone(kcm)
        self.assertEqual(kcm.contactmoment.url, data.contactmoment["url"])
        resolved_contactmoment_requests = [
            req
            for req in m.request_history
            if req.url == data.contactmoment["url"]
            or req.url == data.contactmoment_intern["url"]
        ]
        self.assertEqual(len(resolved_contactmoment_requests), 1)
        self.assertEqual(
            resolved_contactmoment_requests[0].url, data.contactmoment["url"]
        )

    def test_fetch_klantcontactmoment_returns_none_when_not_found(self, m):
        data = MockAPIReadData().install_mocks(m)

        kcm = self.service.fetch_klantcontactmoment(
            "00000000-0000-0000-0000-000000000000", user_bsn=data.user.bsn
        )

        self.assertIsNone(kcm)

    def test_fetch_klantcontactmoment_returns_none_when_resolution_fails(self, m):
        data = MockAPIReadData().install_mocks(m)
        m.get(data.contactmoment["url"], status_code=500)

        kcm = self.service.fetch_klantcontactmoment(
            data.klant_contactmoment["uuid"], user_bsn=data.user.bsn
        )

        self.assertIsNone(kcm)

    def test_retrieve_klantcontactmomenten_for_klant_reports_list_failure(self, m):
        """A failing list call must be reported, not raised.

        Otherwise one klant's failure (e.g. one vestiging of a multi-vestiging KVK)
        would abort every klant already processed in the same request.
        """
        data = MockAPIReadData().install_mocks(m)
        m.get(
            f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten?klant={data.klant_bsn['url']}",
            status_code=500,
        )
        klant = build_klanten_client().retrieve_klant(user_bsn=data.user.bsn)

        result = self.service.retrieve_klantcontactmomenten_for_klant(klant)

        self.assertEqual(result.klantcontactmomenten, [])
        self.assertEqual(result.skipped, [])
        self.assertTrue(result.list_fetch_failed)
        self.assertTrue(result.is_incomplete)

    def test_retrieve_question_returns_expected_result(self, m):
        data = MockAPIReadData().install_mocks(m)
        config = ESuiteKlantConfig.get_solo()

        for user, params, expected_klantcontact, expected_contactmoment, use_rsin in (
            (
                data.user,
                {"user_bsn": "100000001"},
                data.klant_contactmoment,
                data.contactmoment,
                False,
            ),
            (
                data.eherkenning_user,
                {"user_kvk_or_rsin": "12345678"},
                data.klant_contactmoment2,
                data.contactmoment2,
                False,
            ),
            (
                data.eherkenning_user,
                {"user_kvk_or_rsin": "12345678", "vestigingsnummer": "1234"},
                data.klant_contactmoment4,
                data.contactmoment_vestiging,
                False,
            ),
            (
                data.eherkenning_user,
                # RSIN case
                {"user_kvk_or_rsin": "000000000", "vestigingsnummer": "1234"},
                data.klant_contactmoment4,
                data.contactmoment_vestiging,
                True,
            ),
            (
                data.eherkenning_user,
                # RSIN case
                {"user_kvk_or_rsin": "000000000"},
                data.klant_contactmoment2,
                data.contactmoment2,
                True,
            ),
        ):
            with self.subTest(f"{user=} {params=} {use_rsin=}"):
                config.use_rsin_for_innNnpId_query_parameter = use_rsin
                config.save()

                question, _ = self.service.retrieve_question(
                    params, expected_klantcontact["uuid"], user
                )

                self.assertEqual(
                    question,
                    {
                        "identification": expected_contactmoment["identificatie"],
                        "api_source_url": expected_contactmoment["url"],
                        "api_source_uuid": uuid_from_url(expected_contactmoment["url"]),
                        "subject": self.contactformsubject.subject,
                        "question_text": expected_contactmoment["tekst"],
                        "answer_text": expected_contactmoment["antwoord"],
                        "registered_date": datetime.fromisoformat(
                            expected_contactmoment["registratiedatum"]
                        ),
                        "status": Status.afgehandeld.label,
                        "channel": expected_contactmoment["kanaal"],
                        "new_answer_available": False,
                        "api_service": KlantenServiceType.ESUITE,
                    },
                )
                m.reset_mock()
