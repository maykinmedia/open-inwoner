import logging  # noqa: TID251 - only used for log levels
from unittest.mock import Mock, patch

from django.test import RequestFactory, TestCase, override_settings

import requests_mock
from freezegun import freeze_time
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import RolTypes, VertrouwelijkheidsAanduidingen

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openzaak.api.views import ZakenNotificationsWebhookView
from open_inwoner.openzaak.api_models import Status, StatusType, Zaak, ZaakType
from open_inwoner.openzaak.models import OpenZaakConfig, UserCaseStatusNotification
from open_inwoner.openzaak.notifications import (
    _handle_status_update,
    handle_zaken_notification,
)
from open_inwoner.utils.test import ClearCachesMixin, paginated_response
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin, Lookups

from .factories import (
    NotificationFactory,
    ZaakTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
)
from .helpers import copy_with_new_uuid
from .shared import ZAKEN_ROOT
from .test_notification_data import MockAPIData, MockAPIDataAlt


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
@requests_mock.Mocker()
@patch("open_inwoner.openzaak.notifications._handle_status_update", autospec=True)
class StatusNotificationHandlerTestCase(
    AssertTimelineLogMixin, ClearCachesMixin, TestCase
):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIData.setUpServices()
        MockAPIDataAlt.setUpServices()

    def test_handle_zaak_status_notifications(self, m, mock_handle: Mock):
        """
        Happy flow (with multiple ZGW backends) for notifications about zaak status updates
        """
        data = MockAPIData().install_mocks(m)
        data_alt = MockAPIDataAlt().install_mocks(m)

        self.clearTimelineLogs()

        # Added for https://taiga.maykinmedia.nl/project/open-inwoner/task/1904
        # In eSuite it is possible to reuse a StatusType for multiple ZaakTypen, which
        # led to errors when retrieving the ZaakTypeStatusTypeConfig. This duplicate
        # config is added to verify that that issue was solved
        ztc = ZaakTypeConfigFactory.create(
            catalogus__url=data.zaak_type["catalogus"],
            identificatie=data.zaak_type["identificatie"],
        )
        ZaakTypeStatusTypeConfigFactory.create(
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
        )

        # additional configs for testing multiple backends
        ztc2 = ZaakTypeConfigFactory.create(
            catalogus__url=data_alt.zaak_type_alt["catalogus"],
            identificatie=data_alt.zaak_type_alt["identificatie"],
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc2,
            omschrijving=data_alt.status_type_final_alt["omschrijving"],
            statustype_url=data_alt.status_type_final_alt["url"],
        )

        request = RequestFactory().get("/")
        webhook_view = ZakenNotificationsWebhookView()
        webhook_view.setup(request)

        config = SiteConfiguration.get_solo()
        config.notifications_cases_enabled = True
        config.save()

        for idx, (api_group, notification, zaak, status, user_initiator) in enumerate(
            [
                (
                    data.api_group,
                    data.status_notification,
                    data.zaak,
                    data.status_final,
                    data.user_initiator,
                ),
                (
                    data_alt.api_group_alt,
                    data_alt.status_notification_alt,
                    data_alt.zaak_alt,
                    data_alt.status_final_alt,
                    data_alt.user_initiator_alt,
                ),
            ]
        ):
            with self.subTest(f"api_group_{idx}"):
                handle_zaken_notification(notification)

                mock_handle.assert_called()

                # check call arguments
                args = mock_handle.call_args.args
                self.assertEqual(args[0], notification)
                self.assertEqual(args[1], user_initiator)
                self.assertEqual(args[2].url, zaak["url"])
                self.assertEqual(args[3].url, status["url"])

        log_dump = self.getTimelineLogDump()
        self.assertIn("total 2 timelinelogs", log_dump)
        self.assertIn(
            "accepted status notification: attempt informing users ", log_dump
        )
        self.assertIn(data.user_initiator.email, log_dump)
        self.assertIn(data_alt.user_initiator_alt.email, log_dump)

    # start of generic checks

    def test_no_api_group_found(self, m, mock_handle: Mock):
        data = MockAPIData().install_mocks(m)

        # API group is resolved from zaak url == hoofd_object
        data.status_notification.hoofd_object = "http://www.bogus.com"

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()

    def test_status_bails_when_bad_notification_channel(self, m, mock_handle: Mock):
        notification = NotificationFactory(kanaal="not_zaken")
        with self.assertRaisesRegex(
            Exception, r"^handler expects kanaal 'zaken' but received 'not_zaken'"
        ):
            handle_zaken_notification(notification)

        mock_handle.assert_not_called()

    def test_status_bails_when_bad_notification_resource(self, m, mock_handle: Mock):
        notification = NotificationFactory(resource="not_status")

        handle_zaken_notification(notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored not_status notification: resource is not 'status' or 'zaakinformatieobject' but 'not_status' for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_no_roles_found_for_case(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["case_roles"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: cannot retrieve rollen for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_handle_zaak_status_notifications_with_betrokkene_type_flag(
        self, m, mock_handle: Mock
    ):
        """
        Happy path when fetch_rollen_with_betrokkene_type=True: roles are fetched per
        betrokkene type and the handler correctly finds users and proceeds.
        """
        MockAPIData.api_group.fetch_rollen_with_betrokkene_type = True
        MockAPIData.api_group.save()

        data = MockAPIData().install_mocks(m)
        zaak_url = data.zaak["url"]
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={zaak_url}&betrokkeneType={RolTypes.natuurlijk_persoon}",
            json=paginated_response(data.case_roles),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={zaak_url}&betrokkeneType={RolTypes.niet_natuurlijk_persoon}",
            json=paginated_response([]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={zaak_url}&betrokkeneType={RolTypes.vestiging}",
            json=paginated_response([]),
        )

        ztc = ZaakTypeConfigFactory.create(
            catalogus__url=data.zaak_type["catalogus"],
            identificatie=data.zaak_type["identificatie"],
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_called_once()
        args = mock_handle.call_args.args
        self.assertEqual(args[1], data.user_initiator)
        self.assertEqual(args[2].url, data.zaak["url"])

    def test_status_bails_when_no_roles_found_with_betrokkene_type_flag(
        self, m, mock_handle: Mock
    ):
        """
        When fetch_rollen_with_betrokkene_type=True, empty results across all betrokkene
        type queries means no initiators can be found, so the handler bails.
        """
        MockAPIData.api_group.fetch_rollen_with_betrokkene_type = True
        MockAPIData.api_group.save()

        data = MockAPIData().install_mocks(m)
        zaak_url = data.zaak["url"]
        for betrokkene_type in RolTypes:
            m.get(
                f"{ZAKEN_ROOT}rollen?zaak={zaak_url}&betrokkeneType={betrokkene_type}",
                json=paginated_response([]),
            )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: no users with bsn/nnp_id as (mede)initiators in zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_no_emailable_users_are_found_for_roles(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.user_initiator.delete()
        data.install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: no users with bsn/nnp_id as (mede)initiators in zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_cannot_fetch_case(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: cannot retrieve zaak https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_status_bails_when_cannot_fetch_case_type(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak_type"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: cannot retrieve zaaktype https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_status_bails_when_case_not_visible_because_confidentiality(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.zaak["vertrouwelijkheidaanduiding"] = VertrouwelijkheidsAanduidingen.geheim
        data.install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: zaak not visible after applying website visibility filter for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_case_not_visible_because_internal_case(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.zaak_type["indicatieInternOfExtern"] = "intern"
        data.install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: zaak not visible after applying website visibility filter for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    # end of generic checks

    # start of status specific checks

    def test_status_bails_when_cannot_fetch_status_history(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["status_history"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: cannot retrieve status_history for zaak https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_status_bails_when_status_history_is_single_initial_item(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.status_history = [data.status_initial]
        data.install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: skip initial status notification for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_cannot_fetch_status_type(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["status_type_final"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: cannot retrieve status_type {data.status_type_final['url']} for zaak https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_status_bails_when_status_type_not_marked_as_informeren(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.status_type_final["informeren"] = False
        data.install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: status_type.informeren is false for status {data.status_final['url']} and zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_skip_informeren_is_set_and_no_zaaktypeconfig_is_found(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: 'skip_notification_statustype_informeren' is True but cannot retrieve zaaktype configuration '{data.zaak_type['identificatie']}' for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_skip_informeren_is_set_and_no_zaaktypeconfig_is_found_from_zaaktype_none_catalog(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: 'skip_notification_statustype_informeren' is True but cannot retrieve zaaktype configuration '{data.zaak_type['identificatie']}' for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_handle_notification_when_skip_informeren_is_set_and_zaaktypeconfig_is_found(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData().install_mocks(m)

        ztc = ZaakTypeConfigFactory.create(
            catalogus__url=data.zaak_type["catalogus"],
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )
        # Added for https://taiga.maykinmedia.nl/project/open-inwoner/task/1904
        # In eSuite it is possible to reuse a StatusType for multiple ZaakTypen, which
        # led to errors when retrieving the ZaakTypeStatusTypeConfig. This duplicate
        # config is added to verify that that issue was solved
        ZaakTypeStatusTypeConfigFactory.create(
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_called_once()

        # check call arguments
        args = mock_handle.call_args.args
        self.assertEqual(args[0], data.status_notification)
        self.assertEqual(args[1], data.user_initiator)
        self.assertEqual(args[2].url, data.zaak["url"])
        self.assertEqual(args[3].url, data.status_final["url"])

        self.assertTimelineLog(
            "accepted status notification: attempt informing users ",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_handle_notification_status_type_config_notify_false(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData().install_mocks(m)

        zaaktype_config = ZaakTypeConfigFactory.create(
            catalogus__url=data.zaak_type["catalogus"],
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )

        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=zaaktype_config,
            statustype_url=data.status_type_final["url"],
            notify_status_change=False,
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()

        self.assertTimelineLog(
            "ignored status notification: 'notify_status_change' is False",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_skip_informeren_is_set_and_zaaktypeconfig_is_found_but_not_set(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        ZaakTypeConfigFactory.create(
            catalogus__url=data.zaak_type["catalogus"],
            identificatie=data.zaak_type["identificatie"],
            notify_status_changes=False,
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: zaaktype configuration '{data.zaak_type['identificatie']}' found but 'notify_status_changes' is False for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_skip_informeren_is_set_and_zaaktypeconfig_is_not_found_because_different_catalog(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        ZaakTypeConfigFactory.create(
            catalogus__url="http://not-the-catalogus.xyz",
            identificatie=data.zaak_type["identificatie"],
            notify_status_changes=False,
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: 'skip_notification_statustype_informeren' is True but cannot retrieve zaaktype configuration '{data.zaak_type['identificatie']}' for zaak https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_user_status_notifications_disabled(self, m, mock_handle: Mock):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        user = data.user_initiator
        user.cases_notifications = False  # opt-out
        user.save()

        ztc = ZaakTypeConfigFactory.create(
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
            notify_status_change=True,
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()

    def test_action_required_notifications_cannot_be_disabled(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        user = data.user_initiator
        user.cases_notifications = False  # opt-out
        user.save()

        ztc = ZaakTypeConfigFactory.create(
            identificatie=data.zaak_type["identificatie"],
            notify_status_changes=True,
            catalogus__url=data.zaak_type["catalogus"],
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
            notify_status_change=True,
            action_required=True,  # these cannot be disabled by the user
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_called_once()

    def test_user_bad_email(self, m, mock_handle: Mock):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.install_mocks(m)

        user = data.user_initiator
        user.email = "user@example.org"
        user.save()

        ztc = ZaakTypeConfigFactory.create(
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )
        ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
            notify_status_change=True,
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()


@freeze_time("2023-01-01 01:00:00")
class NotificationHandlerUserMessageTestCase(AssertTimelineLogMixin, TestCase):
    """
    note these tests match with a similar test from `test_notification_zaak_infoobject.py`
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIData.setUpServices()
        oz_config = OpenZaakConfig.get_solo()
        oz_config.notification_frequency_limit = 3600
        oz_config.save()

    @patch(
        "open_inwoner.userfeed.hooks.case_status_notification_received", autospec=True
    )
    @patch("open_inwoner.openzaak.notifications.send_case_update_email", autospec=True)
    def test_handle_status_update(self, mock_send: Mock, mock_feed_hook: Mock):
        data = MockAPIData()
        user = data.user_initiator

        zaak = factory(Zaak, data.zaak)
        zaak.zaaktype = factory(ZaakType, data.zaak_type)

        status_initial = factory(Status, data.status_initial)
        status_initial.statustype = factory(StatusType, data.status_type_initial)

        status_final = factory(Status, data.status_final)
        status_final.statustype = factory(StatusType, data.status_type_final)

        ztc = ZaakTypeConfigFactory.create(
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )
        status_type_config_initial = ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_initial["omschrijving"],
            statustype_url=data.status_type_initial["url"],
            notify_status_change=True,
        )
        status_type_config_final = ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
            notify_status_change=True,
            action_required=True,
        )

        # first call
        _handle_status_update(
            data.status_notification,
            user,
            zaak,
            status_initial,
            status_type_config_initial,
            data.api_group,
        )

        mock_send.assert_called_once()
        mock_send.assert_called_with(
            user,
            zaak,
            template_name="case_status_notification",
            api_group=data.api_group,
            status=status_initial,
        )

        # check if userfeed hook was called
        mock_feed_hook.assert_called_once()

        # check call arguments
        args = mock_send.call_args.args
        kwargs = mock_send.call_args.kwargs

        self.assertEqual(args[0], user)
        self.assertEqual(args[1].url, zaak.url)
        self.assertEqual(args[2], "case_status_notification")
        self.assertEqual(kwargs["status"], status_initial)

        mock_send.reset_mock()

        self.assertTimelineLog(
            "sent status notification email for user",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        self.assertEqual(
            1, UserCaseStatusNotification.objects.filter(is_sent=True).count()
        )

        # second call with same zaak/status
        _handle_status_update(
            data.status_notification,
            user,
            zaak,
            status_initial,
            status_type_config_initial,
            data.api_group,
        )

        # no duplicate mail for this user/zaak/status
        mock_send.assert_not_called()

        with self.subTest("mails are throttled based on template_name"):
            # call with different status and different configuration with action_required=True
            _handle_status_update(
                data.status_notification,
                user,
                zaak,
                status_final,
                status_type_config_final,
                data.api_group,
            )

            mock_send.assert_called_once()

            # check call arguments
            args = mock_send.call_args.args
            kwargs = mock_send.call_args.kwargs

            self.assertEqual(args[0], user)
            self.assertEqual(args[1].url, zaak.url)
            self.assertEqual(args[2], "case_status_notification_action_required")
            self.assertEqual(kwargs["status"], status_final)

            mock_send.reset_mock()

        self.assertTimelineLog(
            "ignored duplicate status notification delivery for user ",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
        # other user is fine
        other_user = UserFactory.create()
        _handle_status_update(
            data.status_notification,
            other_user,
            zaak,
            status_initial,
            status_type_config_initial,
            data.api_group,
        )

        mock_send.assert_called_once()

        args = mock_send.call_args.args
        self.assertEqual(args[0], other_user)

        # test frequency-limit check
        mock_send.reset_mock()
        self.clearTimelineLogs()

        # create new status
        status = factory(Status, copy_with_new_uuid(data.status_final))
        status.statustype = factory(
            StatusType, copy_with_new_uuid(data.status_type_final)
        )
        _handle_status_update(
            data.status_notification,
            user,
            zaak,
            status,
            status_type_config_initial,
            data.api_group,
        )

        # not sent because we already send to this user within the frequency
        mock_send.assert_not_called()

        self.assertTimelineLog(
            "blocked over-frequent status notification email for user",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

        # advance time
        with freeze_time("2023-01-01 03:00:00"):
            status = factory(Status, copy_with_new_uuid(data.status_final))
            status.statustype = factory(
                StatusType, copy_with_new_uuid(data.status_type_final)
            )
            _handle_status_update(
                data.status_notification,
                user,
                zaak,
                status,
                status_type_config_initial,
                data.api_group,
            )

            # this one succeeds
            mock_send.assert_called_once()

    @patch(
        "open_inwoner.userfeed.hooks.case_status_notification_received", autospec=True
    )
    @patch("open_inwoner.openzaak.notifications.send_case_update_email", autospec=True)
    def test_action_required_template(self, mock_send: Mock, mock_feed_hook: Mock):
        data = MockAPIData()
        user = data.user_initiator

        zaak = factory(Zaak, data.zaak)
        zaak.zaaktype = factory(ZaakType, data.zaak_type)

        status = factory(Status, data.status_final)
        status.statustype = factory(StatusType, data.status_type_final)

        ztc = ZaakTypeConfigFactory.create(
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )
        status_type_config = ZaakTypeStatusTypeConfigFactory.create(
            zaaktype_config=ztc,
            omschrijving=data.status_type_final["omschrijving"],
            statustype_url=data.status_type_final["url"],
            notify_status_change=True,
            action_required=True,
        )

        _handle_status_update(
            data.status_notification,
            user,
            zaak,
            status,
            status_type_config,
            data.api_group,
        )

        mock_send.assert_called_once()
        # check call arguments
        args = mock_send.call_args.args
        kwargs = mock_send.call_args.kwargs

        self.assertEqual(args[0], user)
        self.assertEqual(args[1].url, zaak.url)
        self.assertEqual(args[2], "case_status_notification_action_required")
        self.assertEqual(kwargs["status"], status)
