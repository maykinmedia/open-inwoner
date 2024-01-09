from typing import Iterable, NamedTuple, Optional

from django.utils.translation import ngettext

from open_inwoner.userfeed.adapter import FeedItem
from open_inwoner.userfeed.choices import FeedItemType


class SummaryLine(NamedTuple):
    text: str
    count: int


def summarize_case_status_changed(
    items: Iterable[FeedItem],
) -> Optional[SummaryLine]:
    num_items = sum(
        1 for item in items if item.type == FeedItemType.case_status_changed
    )
    if num_items:
        return SummaryLine(
            ngettext(
                "In {count} case the status has changed",
                "In {count} cases the status has changed",
                num_items,
            ),
            num_items,
        )


def summarize_action_required(items: Iterable[FeedItem]) -> Optional[SummaryLine]:
    num_items = sum(1 for item in items if item.action_required)
    if num_items:
        return SummaryLine(
            ngettext(
                "In {count} case your action is required",
                "In {count} cases your action is required",
                num_items,
            ),
            num_items,
        )


def summarize_simple_message(items: Iterable[FeedItem]) -> Optional[SummaryLine]:
    num_items = sum(1 for item in items if item.type == FeedItemType.message_simple)
    if num_items:
        return SummaryLine(
            ngettext(
                "There is {count} message",
                "There are {count} messages",
                num_items,
            ),
            num_items,
        )


SUMMARIES = [
    summarize_simple_message,
    summarize_case_status_changed,
    summarize_action_required,
]
