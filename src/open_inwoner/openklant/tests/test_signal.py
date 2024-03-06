from django.contrib.auth import user_logged_in
from django.test import RequestFactory

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import UserFactory, eHerkenningUserFactory
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.tests.data import KLANTEN_ROOT, MockAPIReadData
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.utils.test import (
    ClearCachesMixin,
    DisableRequestLogMixin,
    paginated_response,
)
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin


@requests_mock.Mocker()
class UpdateUserFromLoginSignalAPITestCase(
    ClearCachesMixin, DisableRequestLogMixin, AssertTimelineLogMixin, WebTest
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()

    def setUp(self) -> None:
        super().setUp()

        self.klant = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="new@example.com",
            telefoonnummer="0612345678",
        )

    def test_update_user_after_login(self, m):
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=999993847",
            json=paginated_response([self.klant]),
        )

        user = UserFactory(
            phonenumber="0123456789",
            email="old@example.com",
            login_type=LoginTypeChoices.digid,
            bsn="999993847",
        )

        request = RequestFactory().get("/dummy")
        request.user = user
        user_logged_in.send(User, user=user, request=request)

        user.refresh_from_db()

        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.phonenumber, "0612345678")

        self.assertTimelineLog("retrieved klant for user")
        self.assertTimelineLog(
            "updated user from klant API with fields: email, phonenumber"
        )

    def test_update_eherkenning_user_after_login(self, m):
        user = eHerkenningUserFactory(
            phonenumber="0123456789",
            email="old@example.com",
            kvk="12345678",
            rsin="000000000",
        )

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                user.email = "old@example.com"
                user.phonenumber = "0123456789"
                user.save()
                self.clearTimelineLogs()

                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                identifier = (
                    "000000000" if use_rsin_for_innNnpId_query_parameter else "12345678"
                )
                m.get(
                    f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={identifier}",
                    json=paginated_response([self.klant]),
                )

                request = RequestFactory().get("/dummy")
                request.user = user
                user_logged_in.send(User, user=user, request=request)

                user.refresh_from_db()

                self.assertEqual(user.email, "new@example.com")
                self.assertEqual(user.phonenumber, "0612345678")

                self.assertTimelineLog("retrieved klant for user")
                self.assertTimelineLog(
                    "updated user from klant API with fields: email, phonenumber"
                )

    def test_update_user_after_login_skips_existing_email(self, m):
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=999993847",
            json=paginated_response([self.klant]),
        )

        user = UserFactory(
            phonenumber="0123456789",
            email="old@example.com",
            login_type=LoginTypeChoices.digid,
            bsn="999993847",
        )
        other_user = UserFactory(
            phonenumber="0101010101",
            # uses same email as klant resource
            email="new@example.com",
        )

        request = RequestFactory().get("/dummy")
        request.user = user
        user_logged_in.send(User, user=user, request=request)

        user.refresh_from_db()

        # email didn't change
        self.assertEqual(user.email, "old@example.com")
        self.assertEqual(user.phonenumber, "0612345678")

        self.assertTimelineLog("retrieved klant for user")
        self.assertTimelineLog("updated user from klant API with fields: phonenumber")
