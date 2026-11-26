import pickle
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from django.contrib.sessions.backends.cache import SessionStore
from django.core.cache import cache
from django.core.signing import BadSignature
from django.test import SimpleTestCase, override_settings

from django_redis.client import DefaultClient
from structlog.testing import capture_logs

from open_inwoner.utils.cache.serializers import SignedPickleSerializer
from open_inwoner.utils.decorators import cache as cache_result
from open_inwoner.utils.metrics import cache_signature_invalid

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
        self.metric = self.enterContext(patch.object(cache_signature_invalid, "add"))
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
        self.metric.assert_not_called()

    def test_refuses_unsigned_pickle(self):
        with self.assertRaises(BadSignature):
            self.serializer.loads(pickle.dumps(_Exploit()))

        self.assertEqual(_unpickled_calls, [])
        self.metric.assert_called_once_with(1)

    def test_refuses_tampered_payload(self):
        signature = self.serializer.dumps("harmless").rsplit(b":", 1)[1]
        forged = self.serializer.dumps(_Exploit()).rsplit(b":", 1)[0]

        with self.assertRaises(BadSignature):
            self.serializer.loads(forged + b":" + signature)

        self.assertEqual(_unpickled_calls, [])
        self.metric.assert_called_once_with(1)

    def test_refuses_data_signed_with_another_key(self):
        with override_settings(SECRET_KEY="attacker-key"):
            signed = SignedPickleSerializer({}).dumps(_Exploit())

        with self.assertRaises(BadSignature):
            self.serializer.loads(signed)

        self.assertEqual(_unpickled_calls, [])
        self.metric.assert_called_once_with(1)

    def test_accepts_data_signed_with_fallback_key(self):
        with override_settings(SECRET_KEY="previous-key"):
            signed = SignedPickleSerializer({}).dumps("value")

        with override_settings(
            SECRET_KEY="current-key", SECRET_KEY_FALLBACKS=["previous-key"]
        ):
            self.assertEqual(SignedPickleSerializer({}).loads(signed), "value")

        self.metric.assert_not_called()


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
                            "CLIENT_CLASS": (
                                "open_inwoner.utils.cache.client.SignedPickleClient"
                            ),
                            "SERIALIZER": (
                                "open_inwoner.utils.cache.serializers"
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
        self.metric = self.enterContext(patch.object(cache_signature_invalid, "add"))
        _unpickled_calls.clear()

    def _signed(self, value) -> bytes:
        cache.set("key", value)
        return self.redis.set.call_args.args[1]

    def test_round_trips_values_written_by_the_app(self):
        self.redis.get.return_value = self._signed({"ids": {1, 2}})

        self.assertEqual(cache.get("key"), {"ids": {1, 2}})
        self.metric.assert_not_called()

    def test_unsigned_value_is_a_cache_miss(self):
        self.redis.get.return_value = pickle.dumps(_Exploit())

        with capture_logs() as logs:
            value = cache.get("key", "default")

        self.assertEqual(value, "default")
        self.assertEqual(_unpickled_calls, [])
        self.assertEqual(
            logs, [{"event": "cache_signature_invalid", "log_level": "warning"}]
        )
        self.metric.assert_called_once_with(1)

    def test_value_signed_with_another_key_is_a_cache_miss(self):
        with override_settings(SECRET_KEY="attacker-key"):
            self.redis.get.return_value = SignedPickleSerializer({}).dumps(_Exploit())

        with capture_logs() as logs:
            value = cache.get("key", "default")

        self.assertEqual(value, "default")
        self.assertEqual(_unpickled_calls, [])
        self.assertEqual(
            logs, [{"event": "cache_signature_invalid", "log_level": "warning"}]
        )
        self.metric.assert_called_once_with(1)

    def test_get_many_leaves_out_refused_values(self):
        self.redis.mget.return_value = [
            self._signed("valid"),
            pickle.dumps(_Exploit()),
            None,
        ]

        with capture_logs() as logs:
            values = cache.get_many(["valid", "refused", "missing"])

        self.assertEqual(values, {"valid": "valid"})
        self.assertEqual(_unpickled_calls, [])
        self.assertEqual(
            logs, [{"event": "cache_signature_invalid", "log_level": "warning"}]
        )
        self.metric.assert_called_once_with(1)

    def test_cached_function_recomputes_and_overwrites_refused_value(self):
        @cache_result("lookup")
        def lookup():
            return "fresh"

        self.redis.get.return_value = pickle.dumps(_Exploit())

        with capture_logs():
            self.assertEqual(lookup(), "fresh")

        self.assertEqual(_unpickled_calls, [])
        stored = self.redis.set.call_args.args[1]
        self.assertEqual(SignedPickleSerializer({}).loads(stored), "fresh")
        self.metric.assert_called_once_with(1)

    def test_incr_version_treats_refused_value_as_missing(self):
        self.redis.get.return_value = pickle.dumps(_Exploit())
        self.redis.exists.return_value = 1
        self.redis.ttl.return_value = 60

        with capture_logs(), self.assertRaisesMessage(ValueError, "not found"):
            cache.incr_version("key")

        self.redis.set.assert_not_called()
        self.redis.delete.assert_not_called()
        self.assertEqual(_unpickled_calls, [])
        self.metric.assert_called_once_with(1)

    def test_tampered_session_loads_as_empty(self):
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
        self.metric.assert_called_once_with(1)
