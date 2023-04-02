import logging
from unittest.mock import Mock, patch

from django.test import TestCase

import requests_mock
from notifications_api_common.models import NotificationsConfig
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.notifications import (
    handle_status_update,
    handle_zaken_notification,
)
from open_inwoner.openzaak.tests.factories import (
    NotificationFactory,
    ZaakTypeConfigFactory,
)
from open_inwoner.utils.test import ClearCachesMixin
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin, Lookups

from ..api_models import Status, StatusType, Zaak, ZaakType
from ..models import OpenZaakConfig
from .test_notification_data import MockAPIData


@requests_mock.Mocker()
@patch("open_inwoner.openzaak.notifications.handle_status_update")
class StatusNotificationHandlerTestCase(
    AssertTimelineLogMixin, ClearCachesMixin, TestCase
):
    maxDiff = None
    config: OpenZaakConfig
    note_config: NotificationsConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIData.setUpServices()

    def test_status_handle_zaken_notification(self, m, mock_handle: Mock):
        """
        happy-flow from valid data calls the (mocked) handle_status_update()
        """
        data = MockAPIData().install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_called_once()

        # check call arguments
        args = mock_handle.call_args.args
        self.assertEqual(args[0], data.user_initiator)
        self.assertEqual(args[1].url, data.zaak["url"])
        self.assertEqual(args[2].url, data.status_final["url"])

        self.assertTimelineLog(
            "accepted status notification: attempt informing users ",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    # start of generic checks

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
            "ignored not_status notification: resource is not 'status' or 'zaakinformatieobject' but 'not_status' for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_no_roles_found_for_case(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["case_roles"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored status notification: cannot retrieve rollen for case https://",
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
            "ignored status notification: no users with bsn and valid email as (mede)initiators in case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_cannot_fetch_case(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: cannot retrieve case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_status_bails_when_cannot_fetch_case_type(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak_type"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: cannot retrieve case_type https://",
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
            f"ignored status notification: case not visible after applying website visibility filter for case https://",
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
            f"ignored status notification: case not visible after applying website visibility filter for case https://",
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
            f"ignored status notification: cannot retrieve status_history for case https://",
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
            f"ignored status notification: skip initial status notification for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_bails_when_cannot_fetch_status_type(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["status_type_final"])

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: cannot retrieve status_type {data.status_type_final['url']} for case https://",
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
            f"ignored status notification: status_type.informeren is false for status {data.status_final['url']} and case https://",
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
            f"ignored status notification: 'skip_notification_statustype_informeren' is True but cannot retrieve case_type configuration '{data.zaak_type['identificatie']}' for case https://",
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
        data.zaak_type["catalogus"] = None
        data.install_mocks(m)

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored status notification: 'skip_notification_statustype_informeren' is True but cannot retrieve case_type configuration '{data.zaak_type['identificatie']}' for case https://",
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

        ZaakTypeConfigFactory.create(
            catalogus__url=data.zaak_type["catalogus"],
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_called_once()

        # check call arguments
        args = mock_handle.call_args.args
        self.assertEqual(args[0], data.user_initiator)
        self.assertEqual(args[1].url, data.zaak["url"])
        self.assertEqual(args[2].url, data.status_final["url"])

        self.assertTimelineLog(
            "accepted status notification: attempt informing users ",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_handle_notification_when_skip_informeren_is_set_and_zaaktypeconfig_is_found_from_zaaktype_none_catalog(
        self, m, mock_handle: Mock
    ):
        oz_config = OpenZaakConfig.get_solo()
        oz_config.skip_notification_statustype_informeren = True
        oz_config.save()

        data = MockAPIData()
        data.zaak_type["catalogus"] = None
        data.install_mocks(m)

        ZaakTypeConfigFactory.create(
            catalogus=None,
            identificatie=data.zaak_type["identificatie"],
            # set this to notify
            notify_status_changes=True,
        )

        handle_zaken_notification(data.status_notification)

        mock_handle.assert_called_once()

        # check call arguments
        args = mock_handle.call_args.args
        self.assertEqual(args[0], data.user_initiator)
        self.assertEqual(args[1].url, data.zaak["url"])
        self.assertEqual(args[2].url, data.status_final["url"])

        self.assertTimelineLog(
            "accepted status notification: attempt informing users ",
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
            f"ignored status notification: case_type configuration '{data.zaak_type['identificatie']}' found but 'notify_status_changes' is False for case https://",
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
            f"ignored status notification: 'skip_notification_statustype_informeren' is True but cannot retrieve case_type configuration '{data.zaak_type['identificatie']}' for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )


class NotificationHandlerEmailTestCase(TestCase):
    @patch("open_inwoner.openzaak.notifications.send_case_update_email")
    def test_handle_status_update(self, mock_send: Mock):
        data = MockAPIData()
        user = data.user_initiator

        case = factory(Zaak, data.zaak)
        case.zaaktype = factory(ZaakType, data.zaak_type)

        status = factory(Status, data.status_final)
        status.statustype = factory(StatusType, data.status_type_final)

        # first call
        handle_status_update(user, case, status)

        mock_send.assert_called_once()

        # check call arguments
        args = mock_send.call_args.args
        self.assertEqual(args[0], user)
        self.assertEqual(args[1].url, case.url)

        mock_send.reset_mock()

        # second call with same case/status
        handle_status_update(user, case, status)

        # no duplicate mail for this user/case/status
        mock_send.assert_not_called()

        # other user is fine
        other_user = UserFactory.create()
        handle_status_update(other_user, case, status)

        mock_send.assert_called_once()

        args = mock_send.call_args.args
        self.assertEqual(args[0], other_user)
