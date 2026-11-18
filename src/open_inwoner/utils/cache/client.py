from collections import OrderedDict
from typing import Any

from django.core import signing

from django_redis.client import DefaultClient

# Stands in for a refused value between decode() and get()/get_many()
_REFUSED = object()


class SignedPickleClient(DefaultClient):
    """
    django-redis client that treats a value the serializer refuses as a cache miss.

    Use it together with ``serializers.SignedPickleSerializer``. A refused value
    (unsigned, tampered or signed with an unknown key) is never unpickled. It is
    logged by the serializer, and the read returns the default instead of raising.
    Callers then recompute and overwrite the value, instead of failing until it
    expires (e.g. after rotating ``SECRET_KEY`` without a fallback).
    """

    def decode(self, value: bytes | int) -> Any:
        try:
            return super().decode(value)
        except signing.BadSignature:
            return _REFUSED

    def get(self, key, default=None, version=None, client=None) -> Any:
        value = super().get(key, default=default, version=version, client=client)
        return default if value is _REFUSED else value

    def get_many(self, keys, version=None, client=None) -> OrderedDict:
        values = super().get_many(keys, version=version, client=client)
        return OrderedDict(
            (key, value) for key, value in values.items() if value is not _REFUSED
        )
