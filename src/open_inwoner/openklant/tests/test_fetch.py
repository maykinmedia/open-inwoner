from django.test import TestCase

import requests_mock

from open_inwoner.openklant.api_models import KlantContactMoment
from open_inwoner.openklant.tests.data import MockAPIReadData
from open_inwoner.openklant.wrap import (
    fetch_klantcontactmoment,
    fetch_klantcontactmomenten,
)
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin


@requests_mock.Mocker()
class FetchKlantDataTestCase(ClearCachesMixin, DisableRequestLogMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()

    def test_fetch_klantcontactmomenten_for_bsn(self, m):
        data = MockAPIReadData().install_mocks(m)

        res = fetch_klantcontactmomenten(user_bsn=data.user.bsn)

        self.assertNotEquals(res, list())
        self.assertIsInstance(res[0], KlantContactMoment)
        self.assertEquals(str(res[0].uuid), data.klant_contactmoment["uuid"])

    def test_fetch_klantcontactmoment_for_bsn(self, m):
        data = MockAPIReadData().install_mocks(m)

        kcm = fetch_klantcontactmoment(
            data.klant_contactmoment["uuid"], user_bsn=data.user.bsn
        )

        self.assertIsNotNone(kcm)
        self.assertIsInstance(kcm, KlantContactMoment)
        self.assertEquals(str(kcm.uuid), data.klant_contactmoment["uuid"])

    def test_fetch_klantcontactmomenten_for_kvk(self, m):
        data = MockAPIReadData().install_mocks(m)

        res = fetch_klantcontactmomenten(user_kvk_or_rsin=data.eherkenning_user.kvk)

        self.assertNotEquals(res, list())
        self.assertIsInstance(res[0], KlantContactMoment)
        self.assertEquals(str(res[0].uuid), data.klant_contactmoment2["uuid"])

    def test_fetch_klantcontactmoment_for_kvk(self, m):
        data = MockAPIReadData().install_mocks(m)

        kcm = fetch_klantcontactmoment(
            data.klant_contactmoment2["uuid"],
            user_kvk_or_rsin=data.eherkenning_user.kvk,
        )

        self.assertIsNotNone(kcm)
        self.assertIsInstance(kcm, KlantContactMoment)
        self.assertEquals(str(kcm.uuid), data.klant_contactmoment2["uuid"])
