from unittest.mock import patch

from django.contrib.auth.signals import user_logged_in
from django.test import RequestFactory, TestCase

import requests_mock

from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.models import KlantenSysteemConfig
from open_inwoner.openklant.services import eSuiteVragenService
from open_inwoner.openklant.tasks import warm_klantcontactmomenten_cache_for_user
from open_inwoner.openklant.tests.data import CONTACTMOMENTEN_ROOT, MockAPIReadData
from open_inwoner.utils.test import ClearCachesMixin


class KlantContactMomentenCachingIntegrationTest(ClearCachesMixin, TestCase):
    """
    Integration test covering the full signal -> task -> cache chain.

    warm_klantcontactmomenten_cache_for_user.apply_async is patched to call the
    underlying run() directly, bypassing QueueOnce (which requires Redis) while
    still exercising the full task body.
    """

    def setUp(self):
        super().setUp()
        MockAPIReadData.setUpServices()
        self.config = KlantenSysteemConfig.get_solo()
        self.config.primary_backend = KlantenServiceType.ESUITE.value
        self.config.save()

    @requests_mock.Mocker()
    def test_login_seeds_klantcontactmomenten_cache_for_bsn_user(self, m):
        data = MockAPIReadData().install_mocks(m)

        request = RequestFactory().get("/")
        request.user = data.user

        with patch.object(
            warm_klantcontactmomenten_cache_for_user,
            "apply_async",
            side_effect=lambda *args, **kwargs: (
                warm_klantcontactmomenten_cache_for_user.run(**kwargs["kwargs"])
            ),
        ):
            user_logged_in.send(sender=None, request=request, user=data.user)

        calls_after_login = len(m.request_history)
        self.assertGreater(calls_after_login, 0, "no HTTP calls made during warm-up")

        # Go through the same service call "Mijn vragen" itself uses, so that a hit
        # here means the page really is served from what the warm-up populated.
        eSuiteVragenService().fetch_klantcontactmomenten(user_bsn=data.user.bsn)

        listing_requests = [
            req
            for req in m.request_history
            if req.method == "GET"
            and req.url.startswith(f"{CONTACTMOMENTEN_ROOT}klantcontactmomenten")
        ]
        self.assertEqual(
            len(listing_requests),
            1,
            "listing should have been served from the cache the warm-up populated",
        )

    @requests_mock.Mocker()
    def test_warmup_is_not_dispatched_when_openklant2_is_primary(self, m):
        self.config.primary_backend = KlantenServiceType.OPENKLANT2.value
        self.config.save()

        data = MockAPIReadData().install_mocks(m)

        request = RequestFactory().get("/")
        request.user = data.user

        with patch.object(
            warm_klantcontactmomenten_cache_for_user, "apply_async"
        ) as mock_apply_async:
            user_logged_in.send(sender=None, request=request, user=data.user)

        mock_apply_async.assert_not_called()

    def test_run_is_a_no_op_for_an_unknown_user(self):
        # Must not raise, e.g. if the user was deleted between dispatch and run.
        warm_klantcontactmomenten_cache_for_user.run(user_id=0)
