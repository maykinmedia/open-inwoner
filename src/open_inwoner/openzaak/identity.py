from __future__ import annotations

from dataclasses import dataclass

from django.http import HttpRequest


class UserIdentity:
    @classmethod
    def from_request(cls, request: HttpRequest) -> BSNIdentity | KVKIdentity | None:
        user = request.user
        if not user.is_authenticated:
            return None
        if user.bsn:
            return BSNIdentity(bsn=user.bsn)
        if user.kvk:
            return KVKIdentity(
                kvk=user.kvk,
                rsin=user.rsin or None,
                vestigingsnummer=user.vestiging or None,
            )
        return None


@dataclass(frozen=True)
class BSNIdentity(UserIdentity):
    bsn: str


@dataclass(frozen=True)
class KVKIdentity(UserIdentity):
    kvk: str
    rsin: str | None = None
    vestigingsnummer: str | None = None
