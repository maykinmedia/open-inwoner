from django.test import TestCase

import requests_mock

from open_inwoner.accounts.tests.factories import (
    DigidUserFactory,
    eHerkenningUserFactory,
    eHerkenningVestigingUserFactory,
)
from open_inwoner.openklant.api_models import KlantContactMoment
from open_inwoner.openklant.tests.data import MockAPIReadData
from open_inwoner.openklant.wrap import (
    fetch_klantcontactmoment,
    fetch_klantcontactmomenten,
)
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin

from ..services import OpenKlant2Service, eSuiteKlantenService
from .factories import ESuiteConfigFactory, OpenKlant2ConfigFactory


@requests_mock.Mocker()
class FetchKlantDataTestCase(ClearCachesMixin, DisableRequestLogMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()

    def test_fetch_klantcontactmomenten_for_bsn(self, m):
        data = MockAPIReadData().install_mocks(m)

        res = fetch_klantcontactmomenten(user_bsn=data.user.bsn)

        self.assertNotEqual(res, list())
        self.assertIsInstance(res[0], KlantContactMoment)
        self.assertEqual(str(res[0].uuid), data.klant_contactmoment["uuid"])

    def test_fetch_klantcontactmoment_for_bsn(self, m):
        data = MockAPIReadData().install_mocks(m)

        kcm = fetch_klantcontactmoment(
            data.klant_contactmoment["uuid"], user_bsn=data.user.bsn
        )

        self.assertIsNotNone(kcm)
        self.assertIsInstance(kcm, KlantContactMoment)
        self.assertEqual(str(kcm.uuid), data.klant_contactmoment["uuid"])

    def test_fetch_klantcontactmomenten_for_kvk(self, m):
        data = MockAPIReadData().install_mocks(m)

        res = fetch_klantcontactmomenten(user_kvk_or_rsin=data.eherkenning_user.kvk)

        self.assertNotEqual(res, list())
        self.assertIsInstance(res[0], KlantContactMoment)
        self.assertEqual(str(res[0].uuid), data.klant_contactmoment2["uuid"])

    def test_fetch_klantcontactmoment_for_kvk(self, m):
        data = MockAPIReadData().install_mocks(m)

        kcm = fetch_klantcontactmoment(
            data.klant_contactmoment2["uuid"],
            user_kvk_or_rsin=data.eherkenning_user.kvk,
        )

        self.assertIsNotNone(kcm)
        self.assertIsInstance(kcm, KlantContactMoment)
        self.assertEqual(str(kcm.uuid), data.klant_contactmoment2["uuid"])


class KlantFetchParametersTest(TestCase):
    def test_fetch_params_bsn(self):
        service = OpenKlant2Service(config=OpenKlant2ConfigFactory())
        user = DigidUserFactory()

        params = service.get_fetch_parameters(user)

        self.assertEqual(params, {"user_bsn": user.bsn})

    def test_fetch_params_kvk(self):
        service = OpenKlant2Service(config=OpenKlant2ConfigFactory())
        user = eHerkenningUserFactory()

        params = service.get_fetch_parameters(user)

        self.assertEqual(params, {"user_kvk_or_rsin": user.kvk})

    def test_fetch_params_vestiging(self):
        service = OpenKlant2Service(config=OpenKlant2ConfigFactory())
        user = eHerkenningVestigingUserFactory()

        params = service.get_fetch_parameters(user)

        self.assertEqual(
            params, {"user_kvk_or_rsin": user.kvk, "vestigingsnummer": user.vestiging}
        )

    def test_fetch_params_rsin(self):
        service = eSuiteKlantenService(
            config=ESuiteConfigFactory(use_rsin_for_innNnpId_query_parameter=True)
        )
        user = eHerkenningVestigingUserFactory()

        params = service.get_fetch_parameters(user)

        self.assertEqual(
            params, {"user_kvk_or_rsin": user.rsin, "vestigingsnummer": user.vestiging}
        )
