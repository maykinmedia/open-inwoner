from django.test import TestCase

import requests_mock

from open_inwoner.openklant.models import KlantContactMomentAnswer
from open_inwoner.openklant.tests.data import MockAPIReadData
from open_inwoner.openklant.wrap import (
    fetch_klantcontactmomenten,
    get_kcm_answer_mapping,
)
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin


@requests_mock.Mocker()
class HelpersTestCase(ClearCachesMixin, DisableRequestLogMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()

    def test_get_kcm_answer_mapping(self, m):
        data = MockAPIReadData().install_mocks(m)

        kcms = fetch_klantcontactmomenten(user_bsn=data.user.bsn)

        with self.subTest(
            "running the first time will create KlantContactMomentAnswer"
        ):
            mapping = get_kcm_answer_mapping(
                [kcm.contactmoment for kcm in kcms], data.user
            )

            self.assertEqual(KlantContactMomentAnswer.objects.count(), 1)

            kcm_local = KlantContactMomentAnswer.objects.get()

            self.assertEqual(mapping, {kcms[0].contactmoment.url: kcm_local})
            self.assertEqual(kcm_local.user, data.user)
            self.assertEqual(kcm_local.contactmoment_url, kcms[0].contactmoment.url)
            self.assertEqual(kcm_local.is_seen, False)

        with self.subTest("running function again will ignore existing entries"):
            mapping = get_kcm_answer_mapping(
                [kcm.contactmoment for kcm in kcms], data.user
            )

            self.assertEqual(KlantContactMomentAnswer.objects.count(), 1)
            self.assertEqual(mapping, {kcms[0].contactmoment.url: kcm_local})
