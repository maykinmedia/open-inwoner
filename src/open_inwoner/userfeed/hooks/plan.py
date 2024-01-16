from datetime import datetime

from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from django.utils.translation import ugettext_lazy as _

from open_inwoner.accounts.models import User
from open_inwoner.plans.models import Plan
from open_inwoner.userfeed.adapter import FeedItem
from open_inwoner.userfeed.adapters import register_item_adapter
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.models import FeedItemData


def plan_expiring(user: User, plan: Plan):
    data = {
        "plan_title": plan.title,
        "plan_uuid": plan.uuid,
        "plan_end_date": plan.end_date,
    }

    qs = FeedItemData.objects.filter(
        user=user,
        type=FeedItemType.plan_expiring,
    ).filter_ref_object(plan)

    auto_expire = make_aware(
        datetime(plan.end_date.year, plan.end_date.month, plan.end_date.day)
    )
    if not qs.update(
        display_at=timezone.now(),
        completed_at=None,
        type_data=data,
        auto_expire_at=auto_expire,
    ):
        FeedItemData.objects.create(
            user=user,
            type=FeedItemType.plan_expiring,
            ref_object_field=plan,
            type_data=data,
            action_required=True,
            auto_expire_at=auto_expire,
        )


def plan_completed(user: User, plan: Plan):
    FeedItemData.objects.mark_object_completed(user, FeedItemType.plan_expiring, plan)


class PlanExpiresFeedItem(FeedItem):
    base_title = _("Plan expiring")
    base_message = _("Plan deadline expires at {expire}")

    cms_apps = ["collaborate"]

    @property
    def title(self) -> str:
        return self.get_data("plan_title", super().title)

    @property
    def message(self) -> str:
        date_text = parse_date(self.get_data("plan_end_date")).strftime("%x")
        return self.base_message.format(expire=date_text)

    @property
    def action_url(self) -> str:
        # TODO harden for missing CMS app
        uuid = self.get_data("plan_uuid")
        return reverse("collaborate:plan_detail", kwargs={"uuid": uuid})


register_item_adapter(PlanExpiresFeedItem, FeedItemType.plan_expiring)
