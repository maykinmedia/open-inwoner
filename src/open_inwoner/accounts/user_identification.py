from __future__ import annotations

from dataclasses import dataclass


class UserIdentification:
    pass


@dataclass(frozen=True)
class BSNIdentification(UserIdentification):
    bsn: str


@dataclass(frozen=True)
class KVKIdentification(UserIdentification):
    kvk: str
    rsin: str | None = None
    vestigingsnummer: str | None = None
