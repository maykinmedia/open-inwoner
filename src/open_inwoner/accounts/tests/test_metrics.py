from django.db import connection
from django.test import TransactionTestCase

from opentelemetry.metrics import CallbackOptions, Observation

from open_inwoner.accounts.metrics import count_users

from .factories import DigidUserFactory, UserFactory


class CountUsersTests(TransactionTestCase):
    def test_counts_users_without_keeping_the_connection_open(self):
        UserFactory.create(is_staff=True)
        DigidUserFactory.create()

        observations = count_users(CallbackOptions())

        self.assertEqual(
            list(observations),
            [
                Observation(2, {"scope": "global", "type": "all"}),
                Observation(1, {"scope": "global", "type": "staff"}),
                Observation(0, {"scope": "global", "type": "superuser"}),
                Observation(
                    1, {"scope": "global", "type": "all", "login_type": "default"}
                ),
                Observation(
                    1, {"scope": "global", "type": "all", "login_type": "digid"}
                ),
                Observation(
                    0, {"scope": "global", "type": "all", "login_type": "eherkenning"}
                ),
                Observation(
                    0, {"scope": "global", "type": "all", "login_type": "oidc"}
                ),
            ],
        )
        self.assertIsNone(connection.connection)
