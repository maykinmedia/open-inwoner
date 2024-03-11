from urllib.parse import parse_qs

from django.test import RequestFactory, TestCase

import requests_mock

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.utils.test import ClearCachesMixin

from ..forms import NewsletterSubscriptionForm
from ..models import LapostaConfig, Subscription
from .factories import LapostaListFactory, MemberFactory, SubscriptionFactory

LAPOSTA_API_ROOT = "https://laposta.local/api/v2/"


@requests_mock.Mocker()
class NewsletterSubscriptionFormTestCase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.user = DigidUserFactory()

        self.request = RequestFactory().get("/")
        self.request.user = self.user

        self.config = LapostaConfig.get_solo()
        self.config.api_root = LAPOSTA_API_ROOT
        self.config.basic_auth_username = "username"
        self.config.basic_auth_password = "password"
        self.config.save()

        self.list1 = LapostaListFactory.build(
            list_id="123", name="Nieuwsbrief1", remarks="foo"
        )
        self.list2 = LapostaListFactory.build(
            list_id="456", name="Nieuwsbrief2", remarks="bar"
        )
        self.list3 = LapostaListFactory.build(
            list_id="789", name="Nieuwsbrief3", remarks="baz"
        )

    def setUpMocks(self, m):
        m.get(
            f"{LAPOSTA_API_ROOT}list",
            json={
                "data": [
                    {"list": self.list1.dict()},
                    {"list": self.list2.dict()},
                    {"list": self.list3.dict()},
                ]
            },
        )

    def test_save_form(self, m):
        """
        Verify that the form can create and delete subscriptions
        """
        self.setUpMocks(m)

        SubscriptionFactory.create(list_id="123", member_id="member123", user=self.user)
        SubscriptionFactory.create(list_id="456", member_id="member456", user=self.user)

        form = NewsletterSubscriptionForm(data={}, user=self.user)

        # User already has a subscription for the first two newsletters
        self.assertEqual(form["newsletters"].initial, ["123", "456"])

        form = NewsletterSubscriptionForm(
            data={"newsletters": ["456", "789"]}, user=self.user
        )

        self.assertTrue(form.is_valid())

        post_matcher = m.post(
            f"{LAPOSTA_API_ROOT}member",
            json={
                "member": MemberFactory.build(
                    list_id="789",
                    member_id="member789",
                    email=self.user.email,
                    custom_fields=None,
                ).dict()
            },
        )
        delete_matcher = m.delete(f"{LAPOSTA_API_ROOT}member/member123?list_id=123")

        form.save(self.request)

        self.assertEqual(
            len(post_matcher.request_history),
            1,
            "Subscribe to list if present in the form data (and no subscription exists yet)",
        )

        [post_request] = post_matcher.request_history

        self.assertEqual(
            parse_qs(post_request.body),
            {"list_id": ["789"], "ip": ["127.0.0.1"], "email": [self.user.email]},
        )

        # Because list_id 123 was present in the
        self.assertEqual(
            len(delete_matcher.request_history),
            1,
            "Unsubscribe from list if not present in the form data",
        )

        subscriptions = Subscription.objects.filter(user=self.user)

        self.assertEqual(subscriptions.count(), 2)

        subscription1, subscription2 = subscriptions

        self.assertEqual(subscription1.list_id, "456")
        self.assertEqual(subscription1.member_id, "member456")
        self.assertEqual(subscription2.list_id, "789")
        self.assertEqual(subscription2.member_id, "member789")

    def test_save_form_create_duplicate_subscription(self, m):
        """
        Verify that the client properly handles the scenario where the user is a member
        of the list in the API, but no Subscription exists locally and tries to create one
        """
        self.setUpMocks(m)

        form = NewsletterSubscriptionForm(data={"newsletters": ["789"]}, user=self.user)

        self.assertTrue(form.is_valid())

        post_matcher = m.post(
            f"{LAPOSTA_API_ROOT}member",
            json={
                "error": {
                    "type": "invalid_input",
                    "message": "Email address exists",
                    "code": 204,
                    "parameter": "email",
                    "id": "pqfozv6xqu",
                    "member_id": "member789",
                }
            },
            status_code=400,
        )

        form.save(self.request)

        self.assertEqual(len(post_matcher.request_history), 1)

        subscriptions = Subscription.objects.filter(user=self.user)

        self.assertEqual(subscriptions.count(), 1)

        subscription = subscriptions.get()

        # Subscription should be created locally, based on data returned by API
        self.assertEqual(subscription.list_id, "789")
        self.assertEqual(subscription.member_id, "member789")

    def test_save_form_delete_non_existent_subscription(self, m):
        """
        Verify that the client properly handles the scenario where the user has a
        Subscription to a list locally and tries to delete it, but that relationship
        does not exist in the API
        """
        self.setUpMocks(m)

        SubscriptionFactory.create(list_id="789", member_id="member789", user=self.user)

        form = NewsletterSubscriptionForm(data={"newsletters": []}, user=self.user)

        self.assertTrue(form.is_valid())

        delete_matcher = m.delete(
            f"{LAPOSTA_API_ROOT}member/member789?list_id=789",
            json={
                "error": {
                    "type": "invalid_input",
                    "message": "Unknown member",
                    "code": 203,
                    "parameter": "member_id",
                }
            },
            status_code=400,
        )

        form.save(self.request)

        self.assertEqual(len(delete_matcher.request_history), 1)

        self.assertFalse(Subscription.objects.filter(user=self.user).exists())
