from django.test import TestCase, tag

import requests_mock

from open_inwoner.laposta.client import create_laposta_client
from open_inwoner.laposta.models import LapostaConfig
from open_inwoner.utils.test import ClearCachesMixin

from .factories import MemberFactory

LAPOSTA_API_ROOT = "https://laposta.local/api/v2/"
EMAIL = "user@example.nl"


@tag("laposta")
@requests_mock.Mocker()
class LapostaClientCachingTestCase(ClearCachesMixin, TestCase):
    def setUp(self):
        super().setUp()

        self.config = LapostaConfig.get_solo()
        self.config.api_root = LAPOSTA_API_ROOT
        self.config.basic_auth_username = "username"
        self.config.basic_auth_password = "password"
        self.config.limit_list_selection_to = ["123", "456"]
        self.config.save()

    def _mock_lookups(self, m, subscribed_to: list[str]):
        for list_id in ("123", "456"):
            m.get(
                f"{LAPOSTA_API_ROOT}member/{EMAIL}?list_id={list_id}",
                status_code=200 if list_id in subscribed_to else 404,
                json={},
            )

    def _lookup_requests(self, m) -> list:
        return [
            req
            for req in m.request_history
            if req.method == "GET" and "member/" in req.url
        ]

    def test_subscriptions_are_cached(self, m):
        self._mock_lookups(m, subscribed_to=["123"])
        client = create_laposta_client()

        first = client.get_subscriptions_for_email(EMAIL)
        second = client.get_subscriptions_for_email(EMAIL)

        self.assertEqual(first, ["123"])
        self.assertEqual(second, first)
        self.assertEqual(len(self._lookup_requests(m)), 2, "one lookup per list")

    def test_create_subscription_invalidates_the_lookup(self, m):
        """Subscribing must show up on the very next read.

        The newsletter form reads the subscriptions to decide which boxes are
        ticked, and saving it lands the user straight back on that form, so a stale
        entry would show the state from before they subscribed.
        """
        self._mock_lookups(m, subscribed_to=[])
        client = create_laposta_client()
        client.get_subscriptions_for_email(EMAIL)
        lookups_after_priming = len(self._lookup_requests(m))

        m.post(
            f"{LAPOSTA_API_ROOT}member",
            json={
                "member": MemberFactory.build(
                    list_id="123", member_id="1", email=EMAIL, custom_fields=None
                ).model_dump()
            },
        )
        client.create_subscription("123", _user_data())

        client.get_subscriptions_for_email(EMAIL)

        self.assertGreater(
            len(self._lookup_requests(m)),
            lookups_after_priming,
            "the cached lookup should have been invalidated",
        )

    def test_remove_subscription_invalidates_the_lookup(self, m):
        self._mock_lookups(m, subscribed_to=["123"])
        client = create_laposta_client()
        client.get_subscriptions_for_email(EMAIL)
        lookups_after_priming = len(self._lookup_requests(m))

        m.delete(
            f"{LAPOSTA_API_ROOT}member/{EMAIL}",
            json={
                "member": MemberFactory.build(
                    list_id="123", member_id="1", email=EMAIL, custom_fields=None
                ).model_dump()
            },
        )
        client.remove_subscription("123", EMAIL)

        client.get_subscriptions_for_email(EMAIL)

        self.assertGreater(
            len(self._lookup_requests(m)),
            lookups_after_priming,
            "the cached lookup should have been invalidated",
        )

    def test_configured_lists_are_part_of_the_cache_key(self, m):
        """Changing the configured selection must not serve the previous answer.

        The result only covers the lists that were asked about, so a narrower or
        wider selection is a different question.
        """
        self._mock_lookups(m, subscribed_to=["123"])
        narrow = create_laposta_client()

        self.config.limit_list_selection_to = ["123"]
        self.config.save()
        wide = create_laposta_client()

        self.assertNotEqual(
            narrow.get_subscriptions_for_email.cache_key(narrow, EMAIL),
            wide.get_subscriptions_for_email.cache_key(wide, EMAIL),
        )


def _user_data():
    from open_inwoner.laposta.api_models import UserData

    return UserData(
        ip="127.0.0.1",
        email=EMAIL,
        source_url=None,
        custom_fields={"toestemming": "Ja"},
        options=None,
    )
