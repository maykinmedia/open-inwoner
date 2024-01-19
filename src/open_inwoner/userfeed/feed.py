import dataclasses
from datetime import timedelta
from typing import Iterable

from django.db.models import Q
from django.utils import timezone
from django.utils.html import escape, format_html

from open_inwoner.accounts.models import User
from open_inwoner.cms.utils.page_display import get_active_app_names
from open_inwoner.userfeed.adapter import FeedItem
from open_inwoner.userfeed.adapters import (
    get_item_adapter_class,
    get_types_for_unpublished_cms_apps,
)
from open_inwoner.userfeed.models import FeedItemData
from open_inwoner.userfeed.summarize import SUMMARIES

ACTION_COMPLETED_HISTORY_RANGE = timedelta(minutes=10)


@dataclasses.dataclass()
class Feed:
    items: list[FeedItem] = dataclasses.field(default_factory=list)
    summary: list[str] = dataclasses.field(default_factory=list)

    def has_display(self) -> bool:
        return self.total_items > 0

    def action_required(self) -> int:
        return any(i.action_required for i in self.items)

    @property
    def total_items(self) -> int:
        return len(self.items)

    def __bool__(self):
        return self.has_display()


def wrap_items(items: Iterable[FeedItemData]) -> Iterable[FeedItem]:
    for item in items:
        yield get_item_adapter_class(item.type)(item)


def get_feed(user: User, with_history: bool = False) -> Feed:
    if not user or user.is_anonymous:
        # empty feed
        return Feed()

    # core filters
    display_filter = Q(completed_at__isnull=True)
    if with_history:
        display_filter |= Q(
            completed_at__gt=timezone.now() - ACTION_COMPLETED_HISTORY_RANGE
        )

    data_items = FeedItemData.objects.filter(
        display_filter,
        user=user,
    ).order_by("display_at")

    # filter cms apps
    inactive_types = get_types_for_unpublished_cms_apps(get_active_app_names())
    if inactive_types:
        data_items = data_items.exclude(type__in=inactive_types)

    # wrap
    items = list(wrap_items(data_items))
    feed = Feed(items=items)

    # add summary lines
    for summarize in SUMMARIES:
        line = summarize(items)
        if line:
            html = escape(line.text)
            if "{count}" in html:
                count = format_html("<span>{}</span>", str(line.count))
                html = format_html(html, count=count)
            feed.summary.append(html)

    return feed
