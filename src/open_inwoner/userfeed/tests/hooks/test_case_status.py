from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape, strip_tags
from django.utils.translation import gettext as _, ngettext

from zgw_consumers.api_models.base import factory

from open_inwoner.openzaak.api_models import Status, StatusType, Zaak, ZaakType
from open_inwoner.openzaak.constants import StatusIndicators
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.openzaak.tests.factories import (
    ZaakTypeConfigFactory,
    ZaakTypeStatusTypeConfigFactory,
)
from open_inwoner.openzaak.tests.test_notification_data import MockAPIData
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.feed import get_feed
from open_inwoner.userfeed.hooks.case_status import (
    case_status_notification_received,
    case_status_seen,
)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class FeedHookTest(TestCase):
    def setUp(self):
        MockAPIData.setUpServices()
        self.api_group = ZGWApiGroupConfig.objects.get()

    @patch("open_inwoner.userfeed.feed.get_active_app_names", return_value=["cases"])
    def test_status_update(self, mock_get_active_app_names: Mock):
        data = MockAPIData()
        user = data.user_initiator

        case = factory(Zaak, data.zaak)
        case.zaaktype = factory(ZaakType, data.zaak_type)

        status = factory(Status, data.status_initial)
        status.statustype = factory(StatusType, data.status_type_initial)

        ztc = ZaakTypeConfigFactory(
            identificatie=case.zaaktype.identificatie,
            catalogus__url=case.zaaktype.catalogus,
            catalogus__service=self.api_group.ztc_service,
        )

        case_status_notification_received(user, case, status)

        # check feed
        feed = get_feed(user)
        self.assertEqual(feed.total_items, 1)
        self.assertEqual(len(feed.summary), 1)

        # check item
        item = feed.items[0]
        self.assertEqual(item.type, FeedItemType.case_status_changed)
        self.assertEqual(item.action_required, False)
        self.assertEqual(item.is_completed, False)
        self.assertEqual(item.status_indicator, StatusIndicators.info)
        self.assertEqual(
            strip_tags(item.message),
            escape(_("Case status has been changed to 'initial'")),
        )
        self.assertEqual(item.title, case.omschrijving)
        self.assertEqual(
            item.action_url,
            reverse(
                "cases:case_detail",
                kwargs={"object_id": case.uuid, "api_group_id": self.api_group.id},
            ),
        )

        summary = feed.summary[0]
        expected = ngettext(
            "In {count} case the status has changed",
            "In {count} cases the status has changed",
            1,
        ).format(count=1)
        self.assertEqual(strip_tags(summary), expected)

        # send duplicate notification
        case_status_notification_received(user, case, status)

        feed = get_feed(user)

        # still only one item
        self.assertEqual(feed.total_items, 1)

        # update status
        status2 = factory(Status, data.status_final)
        status2.statustype = factory(StatusType, data.status_type_final)

        # receive status update
        case_status_notification_received(user, case, status2)

        feed = get_feed(user)

        # still only one item
        self.assertEqual(feed.total_items, 1)

        # check item changed
        item = feed.items[0]
        self.assertEqual(
            strip_tags(item.message),
            escape(
                _("Case status has been changed to '{status}'").format(
                    status=status2.statustype.statustekst
                )
            ),
        )
        self.assertEqual(item.title, case.omschrijving)

        # mark as seen
        case_status_seen(user, case)

        # no longer visible
        feed = get_feed(user)
        self.assertEqual(feed.total_items, 0)

        # doesn't break on repeat
        case_status_seen(user, case)
        self.assertEqual(get_feed(user).total_items, 0)

    @patch("open_inwoner.userfeed.feed.get_active_app_names", return_value=["cases"])
    def test_status_update_with_status_type_config(
        self, mock_get_active_app_names: Mock
    ):
        data = MockAPIData()
        user = data.user_initiator

        case = factory(Zaak, data.zaak)
        case.zaaktype = factory(ZaakType, data.zaak_type)

        status = factory(Status, data.status_initial)
        status.statustype = factory(StatusType, data.status_type_initial)

        ztc = ZaakTypeConfigFactory(
            identificatie=case.zaaktype.identificatie,
            catalogus__url=case.zaaktype.catalogus,
            catalogus__service=self.api_group.ztc_service,
        )
        status_config = ZaakTypeStatusTypeConfigFactory(
            zaaktype_config=ztc,
            statustype_url=status.statustype.url,
            status_indicator=StatusIndicators.warning,
            status_indicator_text="my_status_text",
            action_required=True,
        )

        case_status_notification_received(user, case, status)

        # check feed
        feed = get_feed(user)
        self.assertEqual(feed.total_items, 1)
        self.assertEqual(len(feed.summary), 2)

        # check item
        item = feed.items[0]
        self.assertEqual(item.type, FeedItemType.case_status_changed)
        self.assertEqual(item.action_required, True)
        self.assertEqual(item.is_completed, False)
        self.assertEqual(item.status_indicator, StatusIndicators.warning)
        self.assertEqual(item.status_text, "my_status_text")
        self.assertEqual(
            strip_tags(item.message),
            escape(_("Case status has been changed to 'initial'")),
        )
        self.assertEqual(item.title, case.omschrijving)
        self.assertEqual(
            item.action_url,
            reverse(
                "cases:case_detail",
                kwargs={"object_id": case.uuid, "api_group_id": self.api_group.id},
            ),
        )
