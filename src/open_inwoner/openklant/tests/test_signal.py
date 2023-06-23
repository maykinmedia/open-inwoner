from django.contrib.auth import user_logged_in
from django.test import RequestFactory, override_settings

import requests_mock
from django_webtest import WebTest
from zgw_consumers.test import generate_oas_component

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.tests.data import KLANTEN_ROOT, MockAPIReadData
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

    def test_update_user_after_login(self, m):
        MockAPIReadData.setUpOASMocks(m)

        self.klant = generate_oas_component(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="new@example.com",
            telefoonnummer="0612345678",
        )
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

        self.assertTimelineLog("retrieved klant for BSN-user")
        self.assertTimelineLog(
            "updated user from klant API with fields: email, phonenumber"
        )

    def test_update_user_after_login_skips_existing_email(self, m):
        MockAPIReadData.setUpOASMocks(m)

        self.klant = generate_oas_component(
            "kc",
            "schemas/Klant",
            uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="foo@example.com",
            telefoonnummer="0612345678",
        )
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
            email="foo@example.com",
        )

        request = RequestFactory().get("/dummy")
        request.user = user
        user_logged_in.send(User, user=user, request=request)

        user.refresh_from_db()

        # email didn't change
        self.assertEqual(user.email, "old@example.com")
        self.assertEqual(user.phonenumber, "0612345678")

        self.assertTimelineLog("retrieved klant for BSN-user")
        self.assertTimelineLog("updated user from klant API with fields: phonenumber")
