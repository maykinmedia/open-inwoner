from django.test import TestCase

import requests_mock

from open_inwoner.openklant.models import KlantContactMomentAnswer
from open_inwoner.openklant.services import eSuiteVragenService
from open_inwoner.openklant.tests.data import MockAPIReadData
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin


@requests_mock.Mocker()
class KlantHelperTest(ClearCachesMixin, DisableRequestLogMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()

    def test_get_kcm_answer_mapping(self, m):
        data = MockAPIReadData().install_mocks(m)

        kcms = (
            eSuiteVragenService()
            .fetch_klantcontactmomenten(user_bsn=data.user.bsn)
            .klantcontactmomenten
        )

        with self.subTest(
            "running the first time will create KlantContactMomentAnswer"
        ):
            mapping = KlantContactMomentAnswer.objects.get_or_create_mapping(
                data.user, [kcm.contactmoment.url for kcm in kcms]
            )

            self.assertEqual(KlantContactMomentAnswer.objects.count(), 2)

            kcm_answers = KlantContactMomentAnswer.objects.all()

            self.assertEqual(
                mapping,
                {
                    kcms[0].contactmoment.url: kcm_answers[0],
                    kcms[1].contactmoment.url: kcm_answers[1],
                },
            )
            self.assertEqual(kcm_answers[0].user, data.user)
            self.assertEqual(
                kcm_answers[0].contactmoment_url, kcms[0].contactmoment.url
            )
            self.assertEqual(
                kcm_answers[1].contactmoment_url, kcms[1].contactmoment.url
            )
            self.assertIsNone(kcm_answers[0].last_seen_answer_uuid)

        with self.subTest("running function again will ignore existing entries"):
            mapping = KlantContactMomentAnswer.objects.get_or_create_mapping(
                data.user, [kcm.contactmoment.url for kcm in kcms]
            )

            self.assertEqual(KlantContactMomentAnswer.objects.count(), 2)
            self.assertEqual(
                mapping,
                {
                    kcms[0].contactmoment.url: kcm_answers[0],
                    kcms[1].contactmoment.url: kcm_answers[1],
                },
            )
