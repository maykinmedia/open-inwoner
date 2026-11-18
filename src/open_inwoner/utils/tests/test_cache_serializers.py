import pickle
from datetime import datetime, timezone

from django.core.signing import BadSignature
from django.test import SimpleTestCase, override_settings

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
