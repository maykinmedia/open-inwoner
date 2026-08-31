import uuid

from django.test import tag

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.utils.tests.test_migrations import TestSuccessfulMigrations

_ESUITE_CONTACTMOMENT_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-111111111111"


@tag("migrations")
class SeenAnswerMigrationTest(TestSuccessfulMigrations):
    """Migration 0040: the boolean 'KlantContactMomentAnswer.is_seen' flag is
    replaced with 'last_seen_answer_uuid'.

    eSuite holds one answer per contactmoment, so for its rows the flag translates
    exactly. A Klanten API row's url is the question's klantcontact rather than the
    answer's, so nothing there identifies the answer that was read.
    """

    app = "openklant"
    migrate_from = "0039_openklant2config_vragen_cache_timeout_and_more"
    migrate_to = "0040_klantcontactmomentanswer_last_seen_answer_uuid_and_more"

    def setUpBeforeMigration(self, apps):
        KlantContactMomentAnswer = apps.get_model(
            "openklant", "KlantContactMomentAnswer"
        )
        user = UserFactory()

        def _answer(url, is_seen):
            return KlantContactMomentAnswer.objects.create(
                user_id=user.id, contactmoment_url=url, is_seen=is_seen
            ).id

        self.seen_id = _answer(
            f"http://esuite.nl/contactmomenten/{_ESUITE_CONTACTMOMENT_UUID}",
            is_seen=True,
        )
        self.unseen_id = _answer(
            "http://esuite.nl/contactmomenten/aaaaaaaa-aaaa-aaaa-aaaa-222222222222",
            is_seen=False,
        )
        self.without_uuid_id = _answer(
            "http://esuite.nl/contactmomenten/legacy", is_seen=True
        )
        self.batch_ids = [
            _answer(f"http://esuite.nl/contactmomenten/{uuid.uuid4()}", is_seen=True)
            for _ in range(5)
        ]

    def _answers(self):
        return self.apps.get_model("openklant", "KlantContactMomentAnswer").objects

    def test_seen_esuite_answer_is_identified_by_its_contactmoment(self):
        self.assertEqual(
            self._answers().get(id=self.seen_id).last_seen_answer_uuid,
            uuid.UUID(_ESUITE_CONTACTMOMENT_UUID),
        )

    def test_unseen_answer_is_left_alone(self):
        self.assertIsNone(self._answers().get(id=self.unseen_id).last_seen_answer_uuid)

    def test_url_without_uuid_is_skipped_rather_than_failing(self):
        self.assertIsNone(
            self._answers().get(id=self.without_uuid_id).last_seen_answer_uuid
        )

    def test_every_seen_row_is_carried_over(self):
        carried_over = self._answers().filter(
            id__in=self.batch_ids, last_seen_answer_uuid__isnull=False
        )
        self.assertEqual(carried_over.count(), len(self.batch_ids))
