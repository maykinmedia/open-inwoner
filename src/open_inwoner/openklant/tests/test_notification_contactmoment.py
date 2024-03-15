import logging

from django.test import TestCase

import requests_mock
from notifications_api_common.models import NotificationsConfig

from open_inwoner.accounts.models import User
from open_inwoner.openklant.notifications import handle_contactmomenten_notification
from open_inwoner.openzaak.tests.factories import NotificationFactory
from open_inwoner.utils.test import ClearCachesMixin
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin, Lookups

from ..models import OpenKlantConfig
from .data import MockAPIReadData


@requests_mock.Mocker()
class ContactmomentNotificationHandlerTestCase(
    AssertTimelineLogMixin, ClearCachesMixin, TestCase
):
    maxDiff = None
    config: OpenKlantConfig
    note_config: NotificationsConfig

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        MockAPIReadData.setUpServices()

    def test_status_handle_contactmoment_notification_digid_user(self, m):
        """
        happy-flow from valid data calls the (mocked) handle_status_update()
        """
        data = MockAPIReadData().install_mocks(m)

        contactmoment_notification = NotificationFactory(
            resource="contactmoment",
            actie="update",
            resource_url=data.contactmoment["url"],
            hoofd_object=data.contactmoment["url"],
            kanaal="contactmomenten",
        )

        handle_contactmomenten_notification(contactmoment_notification)

        self.assertTimelineLog(
            f"found klantcontactmomenten for {contactmoment_notification.resource_url}",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

        self.assertTimelineLog(
            f"users found linked to {contactmoment_notification.resource_url}: "
            f"{User.objects.filter(bsn=data.user.bsn)}",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

    def test_status_handle_contactmoment_notification_eherkenning_user(self, m):
        """
        happy-flow from valid data calls the (mocked) handle_status_update()
        """
        data = MockAPIReadData().install_mocks(m)

        contactmoment_notification = NotificationFactory(
            resource="contactmoment",
            actie="update",
            resource_url=data.contactmoment2["url"],
            hoofd_object=data.contactmoment2["url"],
            kanaal="contactmomenten",
        )

        handle_contactmomenten_notification(contactmoment_notification)

        self.assertTimelineLog(
            f"found klantcontactmomenten for {contactmoment_notification.resource_url}",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )

        self.assertTimelineLog(
            f"users found linked to {contactmoment_notification.resource_url}: "
            f"{User.objects.filter(kvk=data.eherkenning_user.kvk)}",
            lookup=Lookups.startswith,
            level=logging.INFO,
        )
