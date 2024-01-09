from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from zgw_consumers.api_models.base import factory

from open_inwoner.openzaak.api_models import (
    InformatieObject,
    Zaak,
    ZaakInformatieObject,
    ZaakType,
)
from open_inwoner.openzaak.tests.test_notification_data import MockAPIData
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.feed import get_feed
from open_inwoner.userfeed.hooks.case_document import (
    case_document_added_notification_received,
    case_documents_seen,
)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class FeedHookTest(TestCase):
    @patch("open_inwoner.userfeed.feed.get_active_app_names", return_value=["cases"])
    def test_document_added(self, mock_get_active_app_names: Mock):
        data = MockAPIData()
        user = data.user_initiator

        case = factory(Zaak, data.zaak)
        case.zaaktype = factory(ZaakType, data.zaak_type)

        zio = factory(ZaakInformatieObject, data.zaak_informatie_object)
        zio.informatieobject = factory(InformatieObject, data.informatie_object)

        case_document_added_notification_received(user, case, zio)

        # check feed
        feed = get_feed(user)
        self.assertEqual(feed.total_items, 1)
        self.assertEqual(len(feed.summary), 0)

        # check item
        item = feed.items[0]
        self.assertEqual(item.type, FeedItemType.case_document_added)
        self.assertEqual(item.action_required, False)
        self.assertEqual(item.is_completed, False)
        self.assertEqual(
            item.message,
            _("Case document '{title}' has been added").format(
                title=zio.informatieobject.titel
            ),
        )
        self.assertEqual(item.title, case.omschrijving)
        self.assertEqual(
            item.action_url,
            reverse("cases:case_detail", kwargs={"object_id": case.uuid}),
        )

        # send duplicate notification
        case_document_added_notification_received(user, case, zio)

        feed = get_feed(user)

        # still only one item
        self.assertEqual(feed.total_items, 1)

        # add another document
        zio2 = factory(ZaakInformatieObject, data.zaak_informatie_object_extra)
        zio2.informatieobject = factory(InformatieObject, data.informatie_object_extra)

        case_document_added_notification_received(user, case, zio2)

        feed = get_feed(user)

        # got two items
        self.assertEqual(feed.total_items, 2)

        # mark as seen
        case_documents_seen(user, case)

        # no longer visible
        feed = get_feed(user)
        self.assertEqual(feed.total_items, 0)

        # doesn't break on repeat
        case_documents_seen(user, case)
        self.assertEqual(get_feed(user).total_items, 0)
