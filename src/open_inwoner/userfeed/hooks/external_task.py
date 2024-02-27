import dataclasses
from typing import List

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import OpenTask
from open_inwoner.openzaak.clients import build_client
from open_inwoner.userfeed.adapter import FeedItem
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.models import FeedItemData

from ..adapters import register_item_adapter


class OpenTaskFeedItem(FeedItem):
    base_title = _("Open task")
    base_message = _("Open task that is yet to be completed")

    @property
    def message(self) -> str:
        return self.get_data("naam", super().title)

    @property
    def action_url(self) -> str:
        return self.get_data("formulier_link")


def create_external_task_items(user: User, openstaande_taken: List[OpenTask]):
    existing_uuids = FeedItemData.objects.filter(
        type=FeedItemType.external_task,
        user=user,
    ).values_list("ref_uuid", flat=True)
    existing_uuids = set(str(uuid) for uuid in existing_uuids)

    create_data = []
    for task in openstaande_taken:
        if task.uuid in existing_uuids:
            continue

        data = {
            "user": user,
            "type": FeedItemType.external_task,
            "ref_uuid": task.uuid,
            "action_required": True,
            "type_data": dataclasses.asdict(task),
        }
        create_data.append(FeedItemData(**data))
    FeedItemData.objects.bulk_create(create_data)

    # Mark all tasks with UUIDs not occurring in the fetched results as completed
    completed_uuids = existing_uuids - set(task.uuid for task in openstaande_taken)
    FeedItemData.objects.filter(
        type=FeedItemType.external_task, user=user, ref_uuid__in=completed_uuids
    ).mark_completed()


@receiver(user_logged_in)
def fetch_open_tasks(sender, user, request, *args, **kwargs):
    if user.login_type == LoginTypeChoices.digid:
        if client := build_client("form"):
            tasks = client.fetch_open_tasks(user.bsn)
            create_external_task_items(user, tasks)


register_item_adapter(OpenTaskFeedItem, FeedItemType.external_task)
