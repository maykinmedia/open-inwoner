import pickle
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from django.contrib.sessions.backends.cache import SessionStore
from django.core.cache import cache
from django.core.signing import BadSignature
from django.test import SimpleTestCase, override_settings

from django_redis.client import DefaultClient
from structlog.testing import capture_logs

from open_inwoner.utils.cache_serializers import SignedPickleSerializer

_unpickled_calls = []


def _record_unpickle(*args):
    _unpickled_calls.append(args)


class _Exploit:
    def __reduce__(self):
        return (_record_unpickle, ("pwned",))


@override_settings(SECRET_KEY="current-key", SECRET_KEY_FALLBACKS=[])
class SignedPickleSerializerTest(SimpleTestCase):
    def setUp(self):
        self.serializer = SignedPickleSerializer({})
        _unpickled_calls.clear()

    def test_round_trips_python_objects(self):
        value = {
            "when": datetime(2026, 11, 18, 12, 30, tzinfo=timezone.utc),
            "ids": {1, 2},
        }

        self.assertEqual(
            self.serializer.loads(self.serializer.dumps(value)),
            value,
        )

    def test_refuses_unsigned_pickle(self):
        with self.assertRaises(BadSignature):
            self.serializer.loads(pickle.dumps(_Exploit()))

        self.assertEqual(_unpickled_calls, [])

    def test_refuses_tampered_payload(self):
        signature = self.serializer.dumps("harmless").rsplit(b":", 1)[1]
        forged = self.serializer.dumps(_Exploit()).rsplit(b":", 1)[0]

        with self.assertRaises(BadSignature):
            self.serializer.loads(forged + b":" + signature)

        self.assertEqual(_unpickled_calls, [])

    def test_refuses_data_signed_with_another_key(self):
        with override_settings(SECRET_KEY="attacker-key"):
            signed = SignedPickleSerializer({}).dumps(_Exploit())

        with self.assertRaises(BadSignature):
            self.serializer.loads(signed)

        self.assertEqual(_unpickled_calls, [])

    def test_accepts_data_signed_with_fallback_key(self):
        with override_settings(SECRET_KEY="previous-key"):
            signed = SignedPickleSerializer({}).dumps("value")

        with override_settings(
            SECRET_KEY="current-key", SECRET_KEY_FALLBACKS=["previous-key"]
        ):
            self.assertEqual(SignedPickleSerializer({}).loads(signed), "value")


@override_settings(
    SECRET_KEY="current-key",
    SECRET_KEY_FALLBACKS=[],
    SESSION_ENGINE="django.contrib.sessions.backends.cache",
    SESSION_CACHE_ALIAS="default",
)
class SignedRedisCacheTest(SimpleTestCase):
    """
    Read values through django-redis, like the app does, with the Redis
    connection replaced by a mock that returns the stored bytes.
    """

    def setUp(self):
        # Applied per test, so every test gets a fresh cache client (and connection)
        self.enterContext(
            override_settings(
                CACHES={
                    "default": {
                        "BACKEND": "django_redis.cache.RedisCache",
                        "LOCATION": "redis://redis.invalid:6379/0",
                        "OPTIONS": {
                            "CLIENT_CLASS": "django_redis.client.DefaultClient",
                            "SERIALIZER": (
                                "open_inwoner.utils.cache_serializers"
                                ".SignedPickleSerializer"
                            ),
                            "IGNORE_EXCEPTIONS": True,
                        },
                    }
                }
            )
        )
        self.redis = Mock()
        self.enterContext(
            patch.object(DefaultClient, "connect", return_value=self.redis)
        )
        _unpickled_calls.clear()

    def test_round_trips_values_written_by_the_app(self):
        cache.set("key", {"ids": {1, 2}})
        stored = self.redis.set.call_args.args[1]
        self.redis.get.return_value = stored

        self.assertEqual(cache.get("key"), {"ids": {1, 2}})

    def test_unsigned_value_fails_the_read(self):
        # IGNORE_EXCEPTIONS only covers connection errors, so this is not a cache miss
        self.redis.get.return_value = pickle.dumps(_Exploit())

        with capture_logs() as logs, self.assertRaises(BadSignature):
            cache.get("key")

        self.assertEqual(_unpickled_calls, [])
        self.assertEqual(
            logs, [{"event": "cache_signature_invalid", "log_level": "warning"}]
        )

    def test_value_signed_with_another_key_fails_the_read(self):
        with override_settings(SECRET_KEY="attacker-key"):
            self.redis.get.return_value = SignedPickleSerializer({}).dumps(_Exploit())

        with capture_logs() as logs, self.assertRaises(BadSignature):
            cache.get("key")

        self.assertEqual(_unpickled_calls, [])
        self.assertEqual(
            logs, [{"event": "cache_signature_invalid", "log_level": "warning"}]
        )

    def test_tampered_session_loads_as_empty(self):
        # Django's cache session backend treats any read error as a missing
        # session, so the user is logged out instead of getting an error
        self.redis.get.return_value = pickle.dumps(_Exploit())
        session = SessionStore(session_key="a" * 32)

        with capture_logs() as logs:
            data = session.load()

        self.assertEqual(data, {})
        self.assertIsNone(session.session_key)
        self.assertEqual(_unpickled_calls, [])
        self.assertEqual(
            logs, [{"event": "cache_signature_invalid", "log_level": "warning"}]
        )
