from dataclasses import dataclass, field
from typing import NotRequired

from typing_extensions import TypedDict


class PartijUpdateData(TypedDict):
    email: NotRequired[str]
    phonenumber: NotRequired[str]
    phonenumber_alternative: NotRequired[str]


@dataclass
class InboundOpenklantSyncResult:
    """
    Outcome of a single run of update_user_from_partij.

    Captures enough detail to drive audit logging and OTEL metrics.
    """

    addresses_created: int = 0
    addresses_updated: int = 0
    addresses_deleted: int = 0
    user_fields_updated: set[str] = field(default_factory=set)
    email_conflicts_skipped: int = 0
    orphaned_addresses_restored: int = 0
    push_back_fired: bool = False
