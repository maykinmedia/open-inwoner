import logging
from unittest.mock import Mock, patch

from django.test import TestCase

import requests_mock
from notifications_api_common.models import NotificationsConfig
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openzaak.notifications import (
    handle_zaakinformatieobject_update,
    handle_zaken_notification,
)
from open_inwoner.openzaak.tests.factories import (
    NotificationFactory,
    ZaakTypeInformatieObjectTypeConfigFactory,
)
from open_inwoner.utils.test import ClearCachesMixin
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin, Lookups

from ..api_models import InformatieObject, Zaak, ZaakInformatieObject, ZaakType
from ..models import OpenZaakConfig, ZaakTypeInformatieObjectTypeConfig
from .test_notification_data import MockAPIData


@requests_mock.Mocker()
@patch("open_inwoner.openzaak.notifications.handle_zaakinformatieobject_update")
class ZaakInformatieObjectNotificationHandlerTestCase(
    AssertTimelineLogMixin, ClearCachesMixin, TestCase
):
    maxDiff = None
    config: OpenZaakConfig
    note_config: NotificationsConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIData.setUpServices()

    def test_zio_handle_zaken_notification(self, m, mock_handle: Mock):
        """
        happy-flow from valid data calls the (mocked) handle_zaakinformatieobject()
        """
        data = MockAPIData().install_mocks(m)

        ZaakTypeInformatieObjectTypeConfigFactory.from_case_type_info_object_dicts(
            data.zaak_type, data.informatie_object, document_notification_enabled=True
        )

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_called_once()

        # check call arguments
        args = mock_handle.call_args.args
        self.assertEqual(args[0], data.user_initiator)
        self.assertEqual(args[1].url, data.zaak["url"])
        self.assertEqual(args[2].url, data.zaak_informatie_object["url"])

        self.assertTimelineLog(
            "accepted zaakinformatieobject notification: attempt informing users ",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    # start of generic checks

    def test_zio_bails_when_bad_notification_channel(self, m, mock_handle: Mock):
        notification = NotificationFactory(kanaal="not_zaken")
        with self.assertRaisesRegex(
            Exception, r"^handler expects kanaal 'zaken' but received 'not_zaken'"
        ):
            handle_zaken_notification(notification)

        mock_handle.assert_not_called()

    def test_zio_bails_when_bad_notification_resource(self, m, mock_handle: Mock):
        notification = NotificationFactory(resource="not_status")

        handle_zaken_notification(notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored not_status notification: resource is not 'status' or 'zaakinformatieobject' but 'not_status' for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_zio_bails_when_no_roles_found_for_case(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["case_roles"])

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored zaakinformatieobject notification: cannot retrieve rollen for case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_zio_bails_when_no_emailable_users_are_found_for_roles(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.user_initiator.delete()
        data.install_mocks(m)

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            "ignored zaakinformatieobject notification: no users with bsn and valid email as (mede)initiators in case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_zio_bails_when_cannot_fetch_case(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak"])

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: cannot retrieve case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_zio_bails_when_cannot_fetch_case_type(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak_type"])

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: cannot retrieve case_type https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_zio_bails_when_case_not_visible_because_confidentiality(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.zaak["vertrouwelijkheidaanduiding"] = VertrouwelijkheidsAanduidingen.geheim
        data.install_mocks(m)

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: case not visible after applying website visibility filter for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_zio_bails_when_case_not_visible_because_internal_case(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.zaak_type["indicatieInternOfExtern"] = "intern"
        data.install_mocks(m)

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: case not visible after applying website visibility filter for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    # end of generic checks

    # start of status specific checks
    def test_zio_bails_when_cannot_fetch_zaak_informatie_object(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.install_mocks(m, res404=["zaak_informatie_object"])

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: cannot retrieve zaakinformatieobject {data.zaak_informatie_object['url']} for case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_zio_bails_when_cannot_fetch_informatie_object(self, m, mock_handle: Mock):
        data = MockAPIData()
        data.install_mocks(m, res404=["informatie_object"])

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: cannot retrieve informatieobject {data.informatie_object['url']} for case https://",
            lookup=Lookups.startswith,
            level=logging.ERROR,
        )

    def test_zio_bails_when_info_object_not_visible_because_confidentiality(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.informatie_object[
            "vertrouwelijkheidaanduiding"
        ] = VertrouwelijkheidsAanduidingen.geheim
        data.install_mocks(m)

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: informatieobject not visible after applying website visibility filter for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_zio_bails_when_info_object_not_visible_because_not_definitive(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData()
        data.informatie_object["status"] = "concept"
        data.install_mocks(m)

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: informatieobject not visible after applying website visibility filter for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_zio_bails_when_zaak_type_info_object_type_config_is_not_found(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData().install_mocks(m)

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: cannot retrieve info_type configuration {data.informatie_object['informatieobjecttype']} and case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_zio_bails_when_zaak_type_info_object_type_config_is_found_not_marked_for_notifications(
        self, m, mock_handle: Mock
    ):
        data = MockAPIData().install_mocks(m)

        ZaakTypeInformatieObjectTypeConfigFactory.from_case_type_info_object_dicts(
            data.zaak_type,
            data.informatie_object,
            document_notification_enabled=False,
            omschrijving="important document",
        )

        handle_zaken_notification(data.zio_notification)

        mock_handle.assert_not_called()
        self.assertTimelineLog(
            f"ignored zaakinformatieobject notification: info_type configuration 'important document' {data.informatie_object['informatieobjecttype']} found but 'document_notification_enabled' is False for case https://",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    # TODO add some no-catalog variations


class NotificationHandlerEmailTestCase(TestCase):
    @patch("open_inwoner.openzaak.notifications.send_case_update_email")
    def test_handle_zaak_info_object_update(self, mock_send: Mock):
        data = MockAPIData()
        user = data.user_initiator

        case = factory(Zaak, data.zaak)
        case.zaaktype = factory(ZaakType, data.zaak_type)

        zio = factory(ZaakInformatieObject, data.zaak_informatie_object)
        zio.informatieobject = factory(InformatieObject, data.informatie_object)

        # first call
        handle_zaakinformatieobject_update(user, case, zio)

        mock_send.assert_called_once()

        # check call arguments
        args = mock_send.call_args.args
        self.assertEqual(args[0], user)
        self.assertEqual(args[1].url, case.url)

        mock_send.reset_mock()

        # second call with same case/status
        handle_zaakinformatieobject_update(user, case, zio)

        # no duplicate mail for this user/case/status
        mock_send.assert_not_called()

        # other user is fine
        other_user = UserFactory.create()
        handle_zaakinformatieobject_update(other_user, case, zio)

        mock_send.assert_called_once()

        args = mock_send.call_args.args
        self.assertEqual(args[0], other_user)
