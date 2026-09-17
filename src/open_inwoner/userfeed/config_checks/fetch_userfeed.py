from typing import Any, Optional, TypedDict

from django import forms
from django.http import HttpRequest
from django.utils.translation import gettext as _

from maykin_config_checks import GenericConfigCheckResult
from maykin_config_checks.permissions import IsSuperUser
from maykin_config_checks.protocols import InteractiveConfigCheck
from maykin_config_checks.registry import registry
from open_inwoner.accounts.models import User
from open_inwoner.cms.utils.page_display import get_active_app_names
from open_inwoner.userfeed.adapters import get_types_for_unpublished_cms_apps
from open_inwoner.userfeed.feed import get_feed
from open_inwoner.userfeed.models import FeedItemData
from open_inwoner.utils.logentry import system_action, user_action


class FetchUserfeedForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label=_("User"),
        help_text=_("User to fetch the feed for"),
    )


class FetchUserfeedCheckParams(TypedDict):
    user: User


class FetchUserfeedCheck(
    InteractiveConfigCheck[
        FetchUserfeedCheckParams,
        User,
    ]
):
    identifier = "fetch_userfeed"
    label = _("Fetch userfeed for user")
    form_class = FetchUserfeedForm

    required_permissions = (IsSuperUser(),)

    @classmethod
    def get_form_kwargs(
        cls,
        instance: Optional[User] = None,
    ) -> dict[str, Any]:
        if instance is not None:
            return {"initial": {"user": instance}}
        return {}

    def run(
        self,
        data: FetchUserfeedCheckParams,
        instance: Optional[User] = None,
        request: Optional[HttpRequest] = None,
    ) -> GenericConfigCheckResult:
        user = data["user"]
        log_message = f"fetch userfeed check run for user {user.pk}"

        if request:
            user_action(request, request.user, log_message)
        else:
            system_action(log_message)

        try:
            feed = get_feed(user)
        except Exception as exc:
            return GenericConfigCheckResult(
                success=False,
                identifier=self.identifier,
                verbose_name=self.label,
                message=_("Unexpected error while fetching userfeed"),
                extra={"exception": str(exc), "type": type(exc).__name__},
            )

        items = feed.items
        total = feed.total_items
        item_summary = [
            {"type": item.type, "action_required": item.action_required}
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

        return GenericConfigCheckResult(
            success=True,
            identifier=self.identifier,
            verbose_name=self.label,
            message=_("%(count)s feed items found") % {"count": total},
            extra={
                "total_items": total,
                "raw_items_count": raw_items.count(),
                "items": item_summary,
                "filtered_out_types": filtered_out_types,
            },
        )


registry.register(FetchUserfeedCheck)
