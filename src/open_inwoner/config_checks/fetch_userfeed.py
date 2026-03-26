from maykin_config_checks import GenericHealthCheckResult

from open_inwoner.cms.utils.page_display import get_active_app_names
from open_inwoner.userfeed.adapters import get_types_for_unpublished_cms_apps
from open_inwoner.userfeed.feed import get_feed
from open_inwoner.userfeed.models import FeedItemData

from .forms import FetchUserfeedConfigCheckParams


class FetchUserfeedCheck:
    identifier = "fetch_userfeed"
    label = "Fetch userfeed for user"
    form_class = FetchUserfeedConfigCheckParams

    def __init__(self, form: FetchUserfeedConfigCheckParams):
        self.form = form

    def run(self, obj) -> GenericHealthCheckResult:
        user = obj

        try:
            feed = get_feed(user)

            items = feed.items
            total = feed.total_items

            item_summary = [
                {
                    "type": item.type,
                    "action_required": item.action_required,
                }
                for item in items
            ]

            raw_items = FeedItemData.objects.filter(user=user)
            inactive_types = get_types_for_unpublished_cms_apps(get_active_app_names())

            filtered_out_types = list(
                raw_items.filter(type__in=inactive_types)
                .values_list("type", flat=True)
                .distinct()
                .order_by("type")
            )

            return GenericHealthCheckResult(
                success=True,
                identifier=self.identifier,
                verbose_name=self.label,
                message=f"Userfeed OK - {total} items found",
                extra={
                    "total_items": total,
                    "raw_items_count": raw_items.count(),
                    "items": item_summary,
                    "filtered_out_types": filtered_out_types,
                },
            )

        except Exception as exc:
            return GenericHealthCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=str(exc),
                extra={"exception": repr(exc)},
            )
