from unittest.mock import call, patch

from django.test import TestCase
from django.utils.translation import gettext as _

import requests_mock
from requests import RequestException

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.cms.plugins.cms_plugins import UserFeedPlugin
from open_inwoner.cms.tests import cms_tools
from open_inwoner.openzaak.tests.factories import ZGWApiGroupConfigFactory
from open_inwoner.openzaak.tests.mocks import ESuiteTaskData
from open_inwoner.openzaak.tests.shared import FORMS_ROOT
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.hooks.external_task import update_user_tasks
from open_inwoner.userfeed.models import FeedItemData
from open_inwoner.userfeed.tests.factories import FeedItemDataFactory


class UserFeedExternalTasksTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory.create(bsn="111111110")

        # services
        ZGWApiGroupConfigFactory(
            form_service__api_root=FORMS_ROOT,
        )

    def test_userfeed_plugin_render_triggers_update_open_tasks(self):
        FeedItemDataFactory.create(
            type=FeedItemType.external_task,
            user=self.user,
            ref_uuid="f3100eea-bef4-44bb-b55b-8715d23fa77f",
            type_data={
                "task_name": "Aanvullende informatie gewenst",
                "task_identificatie": "4321-2023",
                "action_url": "https://maykinmedia.nl",
            },
        )

        with patch("open_inwoner.userfeed.feed.update_user_tasks") as mock:
            html, context = cms_tools.render_plugin(
                UserFeedPlugin, plugin_data={}, user=self.user
            )

            # `cms_tools.render_plugin` renders twice
            mock.assert_has_calls([call(self.user), call(self.user)])

            self.assertIn(f"{_('Open task')} (4321-2023)", html)
            self.assertIn("Aanvullende informatie gewenst", html)

    @requests_mock.Mocker()
    def test_update_user_tasks_create(self, m):
        ESuiteTaskData().install_mocks(m)

        with self.subTest("feed item data created on initial login"):
            update_user_tasks(self.user)

            items_after_first_login = list(FeedItemData.objects.all())

            self.assertEqual(len(items_after_first_login), 2)

            item1, item2 = items_after_first_login

            self.assertEqual(item1.user, self.user)
            self.assertEqual(item1.action_required, True)
            self.assertEqual(item1.type, FeedItemType.external_task)
            self.assertEqual(
                item1.type_data,
                {
                    "task_name": "Aanvullende informatie gewenst",
                    "task_identificatie": "1234-2023",
                    "action_url": "https://maykinmedia.nl",
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
                    "task_name": "Aanvullende informatie gewenst",
                    "task_identificatie": "4321-2023",
                    "action_url": "https://maykinmedia.nl",
                },
            )
            self.assertEqual(
                str(item2.ref_uuid), "d74f6a5c-297d-43a3-a923-1774164d852d"
            )

        with self.subTest("import is idempotent"):
            update_user_tasks(self.user)

            qs_after_second_login = FeedItemData.objects.all()

            self.assertEqual(set(items_after_first_login), set(qs_after_second_login))

    @requests_mock.Mocker()
    def test_update_user_tasks_complete_items(self, m):
        ESuiteTaskData().install_mocks(m)

        old_feed_item = FeedItemDataFactory.create(
            type=FeedItemType.external_task,
            user=self.user,
            ref_uuid="f3100eea-bef4-44bb-b55b-8715d23fa77f",
            type_data={
                "task_name": "Aanvullende informatie gewenst",
                "task_identificatie": "4321-2023",
                "action_url": "https://maykinmedia.nl",
            },
        )

        update_user_tasks(self.user)

        qs_after_first_login = FeedItemData.objects.all()

        self.assertEqual(qs_after_first_login.count(), 3)

        old_feed_item.refresh_from_db()

        self.assertTrue(old_feed_item.is_completed)

    @requests_mock.Mocker()
    def test_update_user_tasks_do_not_complete_items_if_error_occurs(self, m):
        m.get(f"{FORMS_ROOT}openstaande-taken", exc=RequestException)

        old_feed_item = FeedItemDataFactory.create(
            type=FeedItemType.external_task,
            user=self.user,
            ref_uuid="f3100eea-bef4-44bb-b55b-8715d23fa77f",
            type_data={
                "task_name": "Aanvullende informatie gewenst",
                "task_identificatie": "4321-2023",
                "action_url": "https://maykinmedia.nl",
            },
        )

        update_user_tasks(self.user)

        qs_after_first_login = FeedItemData.objects.all()

        self.assertEqual(qs_after_first_login.count(), 1)

        old_feed_item.refresh_from_db()

        self.assertFalse(old_feed_item.is_completed)

    @requests_mock.Mocker()
    def test_update_user_tasks_update_type_data(self, m):
        ESuiteTaskData().install_mocks(m)

        outdated_feed_item = FeedItemDataFactory.create(
            type=FeedItemType.external_task,
            user=self.user,
            ref_uuid="fb72d8db-c3ee-4aa0-96c1-260b202cb208",
            type_data={
                "task_name": "outdated_title",
                "task_identificatie": "outdated_id",
                "action_url": "https://outdated.url",
            },
        )

        update_user_tasks(self.user)

        qs_after_first_login = FeedItemData.objects.all()

        self.assertEqual(qs_after_first_login.count(), 2)

        outdated_feed_item.refresh_from_db()

        self.assertEqual(
            outdated_feed_item.type_data,
            {
                "task_name": "Aanvullende informatie gewenst",
                "task_identificatie": "1234-2023",
                "action_url": "https://maykinmedia.nl",
            },
        )
