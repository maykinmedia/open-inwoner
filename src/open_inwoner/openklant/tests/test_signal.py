from unittest.mock import patch

from django.contrib.auth import user_logged_in
from django.db.models.signals import post_save
from django.test import RequestFactory, tag

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.choices import LoginTypeChoices, NotificationChannelChoice
from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import UserFactory, eHerkenningUserFactory
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.models import ESuiteKlantConfig
from open_inwoner.openklant.tests.data import KLANTEN_ROOT, MockAPIReadData
from open_inwoner.openzaak.tests.helpers import generate_oas_component_cached
from open_inwoner.utils.test import (
    ClearCachesMixin,
    DisableRequestLogMixin,
    paginated_response,
)
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin


@tag("sequential")
@requests_mock.Mocker()
class UpdateUserFromLoginSignalAPITestCase(
    ClearCachesMixin, DisableRequestLogMixin, AssertTimelineLogMixin, WebTest
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()
        config = SiteConfiguration.get_solo()
        config.enable_notification_channel_choice = True
        config.save()

    def setUp(self) -> None:
        super().setUp()

        self.klant_bsn = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "inpBsn": "123456789",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="new@example.com",
            telefoonnummer="0612345678",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )

    def test_update_user_after_login(self, m):
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=999993847",
            json=paginated_response([self.klant_bsn]),
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

    def test_update_notification_channel_choice_after_login(self, m):
        user = UserFactory(
            phonenumber="0123456789",
            email="old@example.com",
            login_type=LoginTypeChoices.digid,
            bsn="999993847",
        )

        for (
            toestemming_zaak_notificaties_alleen_digitaal,
            expected_user_case_notification_channel,
        ) in (
            (True, NotificationChannelChoice.digital_only),
            (False, NotificationChannelChoice.digital_and_post),
            (None, NotificationChannelChoice.digital_and_post),  # The model default
        ):
            with self.subTest(
                f"{toestemming_zaak_notificaties_alleen_digitaal=} leads to"
                f" case notification_channel={expected_user_case_notification_channel}"
            ):
                m.get(
                    f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=999993847",
                    json=paginated_response(
                        [
                            self.klant_bsn
                            | {
                                "toestemmingZaakNotificatiesAlleenDigitaal": toestemming_zaak_notificaties_alleen_digitaal
                            }
                        ]
                    ),
                )
                request = RequestFactory().get("/dummy")
                request.user = user
                user_logged_in.send(User, user=user, request=request)
                user.refresh_from_db()

                self.assertEqual(
                    user.case_notification_channel,
                    expected_user_case_notification_channel,
                )

    def test_update_notification_Channel_choice_after_login_requires_notification_choice_enabled(
        self, m
    ):
        config = SiteConfiguration.get_solo()
        config.enable_notification_channel_choice = False
        config.save()

        user = UserFactory(
            phonenumber="0123456789",
            email="old@example.com",
            login_type=LoginTypeChoices.digid,
            bsn="999993847",
        )
        initial_case_notification_channel = user.case_notification_channel

        for toestemming_zaak_notificaties_alleen_digitaal in (True, False, None):
            with self.subTest(
                f"{toestemming_zaak_notificaties_alleen_digitaal=} has no effect"
                f" if enable_case notification_channel=False"
            ):
                m.get(
                    f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=999993847",
                    json=paginated_response(
                        [
                            self.klant_bsn
                            | {
                                "toestemmingZaakNotificatiesAlleenDigitaal": toestemming_zaak_notificaties_alleen_digitaal
                            }
                        ]
                    ),
                )
                request = RequestFactory().get("/dummy")
                request.user = user
                user_logged_in.send(User, user=user, request=request)
                user.refresh_from_db()

                self.assertEqual(
                    user.case_notification_channel,
                    initial_case_notification_channel,
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
                self.clearTimelineLogs()
                config = ESuiteKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                identifier = (
                    "000000000" if use_rsin_for_innNnpId_query_parameter else "12345678"
                )
                m.get(
                    f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId={identifier}",
                    json=paginated_response([self.klant_bsn]),
                )

                user.email = "old@example.com"
                user.phonenumber = "0123456789"
                user.save()

                # 2 logs: retrieved, updated
                # 1 signal: post_save, get_or_create_klant_for_new_user
                request = RequestFactory().get("/dummy")
                request.user = user
                # Sending this signal will also trigger Django's own
                # update_last_login handler, which in _turn_ will trigger the post_save
                # handler.
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
            json=paginated_response([self.klant_bsn]),
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

    def test_create_klant_for_digid_user(self, m):
        with requests_mock.mock(case_sensitive=True) as m:
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=123456789",
                json={"count": 0, "results": []},
            )
            m.post(f"{KLANTEN_ROOT}klanten", json=self.klant_bsn)

            user = UserFactory(
                login_type=LoginTypeChoices.digid,
                bsn="123456789",
            )

            request = RequestFactory().get("/dummy")
            request.user = user
            user_logged_in.send(User, user=user, request=request)

            self.assertTimelineLog(
                f"created klant ({self.klant_bsn['klantnummer']}) for user"
            )

            requests = m.request_history
            self.assertEqual(len(requests), 2)
            self.assertEqual(
                requests[0].query, f"subjectNatuurlijkPersoon__inpBsn={user.bsn}"
            )
            self.assertEqual(
                requests[1].json(), {"subjectIdentificatie": {"inpBsn": f"{user.bsn}"}}
            )

    def test_create_klant_for_eherkenning_user(self, m):
        klant_eherkenning = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "innNnpId": "87654321",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="new@example.com",
            telefoonnummer="0612345678",
        )

        with requests_mock.mock(case_sensitive=True) as m:
            m.get(
                f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId=87654321",
                json={"count": 0, "results": []},
            )
            m.post(f"{KLANTEN_ROOT}klanten", json=klant_eherkenning)

            user = UserFactory(
                login_type=LoginTypeChoices.eherkenning,
                kvk="87654321",
            )

            request = RequestFactory().get("/dummy")
            request.user = user
            user_logged_in.send(User, user=user, request=request)

            self.assertTimelineLog(
                f"created klant ({klant_eherkenning['klantnummer']}) for user"
            )

            requests = m.request_history
            self.assertEqual(len(requests), 2)
            self.assertEqual(
                requests[0].query, f"subjectNietNatuurlijkPersoon__innNnpId={user.kvk}"
            )
            self.assertEqual(
                requests[1].json(),
                {"subjectIdentificatie": {"innNnpId": f"{user.kvk}"}},
            )


@tag("sequential")
@requests_mock.Mocker()
class CreateKlantForNewUserSignalTestCase(
    ClearCachesMixin, DisableRequestLogMixin, AssertTimelineLogMixin, WebTest
):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()
        config = SiteConfiguration.get_solo()
        config.enable_notification_channel_choice = True
        config.save()

    def setUp(self) -> None:
        super().setUp()

        self.klant_bsn = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "inpBsn": "123456789",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="new@example.com",
            telefoonnummer="0612345678",
            toestemmingZaakNotificatiesAlleenDigitaal=False,
        )

    def test_sync_aborted_for_non_digid_eherkenning(self, m):
        for lt in [
            lt
            for lt in LoginTypeChoices
            if lt not in [LoginTypeChoices.digid, LoginTypeChoices.eherkenning]
        ]:
            with self.subTest(lt):
                with patch(
                    "open_inwoner.accounts.signals._update_esuite_from_user"
                ) as update_func:
                    User.objects.all().delete()
                    user = UserFactory(
                        phonenumber="0123456789",
                        email="old@example.com",
                        login_type=lt,
                        bsn="999993847",
                    )

                    post_save.send(sender=User, instance=user, created=True)
                    update_func.assert_not_called()

    def test_sync_aborted_for_non_created_user(self, m):
        for lt in [LoginTypeChoices.digid, LoginTypeChoices.eherkenning]:
            with self.subTest(lt):
                with patch(
                    "open_inwoner.accounts.signals._update_esuite_from_user"
                ) as update_func:
                    User.objects.all().delete()
                    user = UserFactory(
                        phonenumber="0123456789",
                        email="old@example.com",
                        login_type=lt,
                        bsn="999993847",
                    )

                    post_save.send(sender=User, instance=user, created=False)
                    update_func.assert_not_called()

    def test_sync_aborted_for_existing_klant(self, m):
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=999993847",
            json=paginated_response([self.klant_bsn]),
        )
        with patch(
            "open_inwoner.accounts.signals.eSuiteKlantenService.partial_update_klant"
        ) as update_func:
            user = UserFactory(
                phonenumber="0123456789",
                email="old@example.com",
                login_type=LoginTypeChoices.digid,
                bsn="999993847",
            )

            post_save.send(sender=User, instance=user, created=True)
            update_func.assert_not_called()

    def test_sync_bsn_user_to_esuite_upon_creation(self, m):
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=999993847",
            json=paginated_response([]),
        )
        m.post(
            f"{KLANTEN_ROOT}klanten",
            json=self.klant_bsn,
        )
        m.patch(
            f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            json=self.klant_bsn,
        )

        user = UserFactory(
            phonenumber="0123456789",
            email="old@example.com",
            login_type=LoginTypeChoices.digid,
            bsn="999993847",
        )

        post_save.send(sender=User, instance=user, created=True)

        self.assertEqual(
            m.request_history[1].json(),
            {
                "subjectIdentificatie": {
                    "inpBsn": "999993847",
                }
            },
        )
        self.assertEqual(
            m.request_history[2].json(),
            {
                "emailadres": "old@example.com",
                "telefoonnummer": "0123456789",
                "toestemmingZaakNotificatiesAlleenDigitaal": False,
            },
        )

    def test_sync_bsn_user_to_esuite_upon_creation_without_notificaion_channel(self, m):
        config = SiteConfiguration.get_solo()
        config.enable_notification_channel_choice = False
        config.save()
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNatuurlijkPersoon__inpBsn=999993847",
            json=paginated_response([]),
        )
        m.post(
            f"{KLANTEN_ROOT}klanten",
            json=self.klant_bsn,
        )
        m.patch(
            f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            json=self.klant_bsn,
        )

        user = UserFactory(
            phonenumber="0123456789",
            email="old@example.com",
            login_type=LoginTypeChoices.digid,
            bsn="999993847",
        )

        post_save.send(sender=User, instance=user, created=True)

        self.assertEqual(
            m.request_history[1].json(),
            {
                "subjectIdentificatie": {
                    "inpBsn": "999993847",
                }
            },
        )
        self.assertEqual(
            m.request_history[2].json(),
            {
                "emailadres": "old@example.com",
                "telefoonnummer": "0123456789",
            },
        )

    def test_sync_eherkenning_user_to_esuite_upon_creation(self, m):
        klant_eherkenning = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "innNnpId": "87654321",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="new@example.com",
            telefoonnummer="0612345678",
        )
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId=87654321",
            json={"count": 0, "results": []},
        )
        m.post(f"{KLANTEN_ROOT}klanten", json=klant_eherkenning)
        m.patch(
            f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            json=self.klant_bsn,
        )

        user = UserFactory(
            login_type=LoginTypeChoices.eherkenning,
            kvk="87654321",
        )

        post_save.send(sender=User, instance=user, created=True)

        self.assertEqual(
            m.request_history[1].json(),
            {
                "subjectIdentificatie": {
                    "innNnpId": "87654321",
                }
            },
        )
        self.assertEqual(
            m.request_history[2].json(),
            {
                "emailadres": user.email,
                "telefoonnummer": user.phonenumber,
                "toestemmingZaakNotificatiesAlleenDigitaal": False,
            },
        )

    def test_sync_eherkenning_user_to_esuite_upon_creation_without_notification_channel(
        self, m
    ):
        config = SiteConfiguration.get_solo()
        config.enable_notification_channel_choice = False
        config.save()
        klant_eherkenning = generate_oas_component_cached(
            "kc",
            "schemas/Klant",
            bronorganisatie="123456789",
            klantnummer="12345678",
            subjectIdentificatie={
                "innNnpId": "87654321",
            },
            url=f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            emailadres="new@example.com",
            telefoonnummer="0612345678",
        )
        m.get(
            f"{KLANTEN_ROOT}klanten?subjectNietNatuurlijkPersoon__innNnpId=87654321",
            json={"count": 0, "results": []},
        )
        m.post(f"{KLANTEN_ROOT}klanten", json=klant_eherkenning)
        m.patch(
            f"{KLANTEN_ROOT}klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            json=self.klant_bsn,
        )

        user = UserFactory(
            login_type=LoginTypeChoices.eherkenning,
            kvk="87654321",
        )

        post_save.send(sender=User, instance=user, created=True)

        self.assertEqual(
            m.request_history[1].json(),
            {
                "subjectIdentificatie": {
                    "innNnpId": "87654321",
                }
            },
        )
        self.assertEqual(
            m.request_history[2].json(),
            {
                "emailadres": user.email,
                "telefoonnummer": user.phonenumber,
            },
        )
