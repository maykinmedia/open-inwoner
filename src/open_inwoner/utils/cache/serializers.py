from typing import Any

from django.core import signing

import structlog
from django_redis.serializers.base import BaseSerializer
from django_redis.serializers.pickle import PickleSerializer

from open_inwoner.utils.metrics import cache_signature_invalid

logger = structlog.stdlib.get_logger(__name__)

# Part of every signature: changing it invalidates all cached data
_SALT = "open_inwoner.utils.cache.SignedPickleSerializer"


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
