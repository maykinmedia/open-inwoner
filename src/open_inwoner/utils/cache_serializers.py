from collections import OrderedDict
from typing import Any

from django.core import signing

import structlog
from django_redis.client import DefaultClient
from django_redis.serializers.base import BaseSerializer
from django_redis.serializers.pickle import PickleSerializer

from .metrics import cache_signature_invalid

logger = structlog.stdlib.get_logger(__name__)

_SALT = "open_inwoner.utils.cache_serializers.SignedPickleSerializer"


class SignedPickleSerializer(BaseSerializer):
    """
    Pickle serializer that only unpickles data signed with ``SECRET_KEY``.

    Whoever can write to Redis cannot get their own pickles loaded (RCE). The
    signature is verified (also against ``SECRET_KEY_FALLBACKS``) before unpickling.
    """

    def __init__(self, options):
        super().__init__(options)
        pickle_serializer = PickleSerializer(options)
        self._pickle = lambda: pickle_serializer
        self._signer = signing.Signer(salt=_SALT)

    def dumps(self, value: Any) -> bytes:
        return self._signer.sign_object(
            value, serializer=self._pickle, compress=True
        ).encode()

    def loads(self, value: bytes) -> Any:
        try:
            return self._signer.unsign_object(value.decode(), serializer=self._pickle)
        except (signing.BadSignature, UnicodeDecodeError) as exc:
            logger.warning("cache_signature_invalid")
            cache_signature_invalid.add(1)
            raise signing.BadSignature(
                "Refusing to unpickle unsigned or tampered cache data"
            ) from exc


# Stands in for a refused value between decode() and get()/get_many()
_REFUSED = object()


class SignedPickleClient(DefaultClient):
    """
    django-redis client that treats a value the serializer refuses as a cache miss.

    Use it together with ``SignedPickleSerializer``. A refused value (unsigned,
    tampered or signed with an unknown key) is never unpickled. It is logged by the
    serializer, and the read returns the default instead of raising. Callers then
    recompute and overwrite the value, instead of failing until it expires (e.g.
    after rotating ``SECRET_KEY`` without a fallback).
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
