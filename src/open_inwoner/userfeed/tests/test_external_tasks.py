from django.contrib.auth import user_logged_in
from django.test import RequestFactory, TestCase

import requests_mock
from zgw_consumers.test.factories import ServiceFactory

from open_inwoner.accounts.models import User
from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.tests.mocks import ESuiteData
from open_inwoner.openzaak.tests.shared import FORMS_ROOT
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.models import FeedItemData
from open_inwoner.userfeed.tests.factories import FeedItemDataFactory


class UserFeedExternalTasksTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory.create(bsn="111111110")

        self.config = OpenZaakConfig.get_solo()
        self.config.form_service = ServiceFactory(api_root=FORMS_ROOT)
        self.config.save()

    @requests_mock.Mocker()
    def test_fetch_tasks_after_login(self, m):
        request = RequestFactory().get("/dummy")
        request.user = self.user

        ESuiteData().install_mocks(m)

        user_logged_in.send(User, user=self.user, request=request)

        qs_after_first_login = FeedItemData.objects.all()

        with self.subTest("feed item data created on initial login"):
            self.assertEqual(qs_after_first_login.count(), 2)

            item1, item2 = qs_after_first_login

            self.assertEqual(item1.user, self.user)
            self.assertEqual(item1.action_required, True)
            self.assertEqual(item1.type, FeedItemType.external_task)
            self.assertEqual(
                item1.type_data,
                {
                    "url": "https://maykinmedia.nl",
                    "naam": "Aanvullende informatie gewenst",
                    "uuid": "fb72d8db-c3ee-4aa0-96c1-260b202cb208",
                    "startdatum": "2023-11-14",
                    "identificatie": "1234-2023",
                    "formulier_link": "https://maykinmedia.nl",
                },
            )
            self.assertEqual(
                str(item1.ref_uuid), "fb72d8db-c3ee-4aa0-96c1-260b202cb208"
            )

            self.assertEqual(item2.user, self.user)
            self.assertEqual(item2.action_required, True)
            self.assertEqual(item2.type, FeedItemType.external_task)
            self.assertEqual(
                item2.type_data,
                {
                    "url": "https://maykinmedia.nl",
                    "naam": "Aanvullende informatie gewenst",
                    "uuid": "d74f6a5c-297d-43a3-a923-1774164d852d",
                    "startdatum": "2023-10-11",
                    "identificatie": "4321-2023",
                    "formulier_link": "https://maykinmedia.nl",
                },
            )
            self.assertEqual(
                str(item2.ref_uuid), "d74f6a5c-297d-43a3-a923-1774164d852d"
            )

        with self.subTest("import is idempotent"):
            user_logged_in.send(User, user=self.user, request=request)

            qs_after_second_login = FeedItemData.objects.all()

            self.assertEqual(set(qs_after_first_login), set(qs_after_second_login))

    @requests_mock.Mocker()
    def test_complete_tasks_after_login(self, m):
        request = RequestFactory().get("/dummy")
        request.user = self.user

        ESuiteData().install_mocks(m)

        old_feed_item = FeedItemDataFactory.create(
            type=FeedItemType.external_task,
            user=self.user,
            ref_uuid="f3100eea-bef4-44bb-b55b-8715d23fa77f",
            type_data={
                "url": "https://maykinmedia.nl",
                "naam": "Aanvullende informatie gewenst",
                "uuid": "d74f6a5c-297d-43a3-a923-1774164d852d",
                "startdatum": "2023-10-11",
                "identificatie": "4321-2023",
                "formulier_link": "https://maykinmedia.nl",
            },
        )

        user_logged_in.send(User, user=self.user, request=request)

        qs_after_first_login = FeedItemData.objects.all()

        self.assertEqual(qs_after_first_login.count(), 3)

        old_feed_item.refresh_from_db()

        self.assertTrue(old_feed_item.is_completed)
