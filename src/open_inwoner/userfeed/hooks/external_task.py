import logging

from django.utils.translation import gettext_lazy as _

from requests import RequestException

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.models import User
from open_inwoner.openzaak.api_models import OpenTask
from open_inwoner.openzaak.clients import build_forms_client
from open_inwoner.userfeed.adapter import FeedItem
from open_inwoner.userfeed.choices import FeedItemType
from open_inwoner.userfeed.models import FeedItemData
from open_inwoner.utils.api import ClientError

from ..adapters import register_item_adapter

logger = logging.getLogger(__name__)


class OpenTaskFeedItem(FeedItem):
    base_title = _("Open task")
    extra_title = _("Case number")
    base_message = _("Open task that is yet to be completed")

    @property
    def title(self) -> str:
        return (
            f"{self.base_title} {self.get_data('task_identificatie')} "
            f"({self.extra_title}: {self.get_data('zaak_identificatie')})"
        )

    @property
    def message(self) -> str:
        return self.get_data("task_name", super().message)


def update_external_task_items(user: User, openstaande_taken: list[OpenTask]):
    """
    Creates items for OpenTasks if they do not exist yet, updates existing items if the
    data changed and marks existing items as complete if no OpenTask exists for that
    uuid anymore
    """
    existing_uuid_mapping = {
        str(item.ref_uuid): item
        for item in FeedItemData.objects.filter(
            type=FeedItemType.external_task,
            user=user,
        )
    }
    existing_uuids = set(existing_uuid_mapping.keys())

    update_data = []
    create_data = []
    for task in openstaande_taken:
        type_data = {
            "action_url": task.formulier_link,
            "task_name": task.naam,
            "task_identificatie": task.identificatie,
            "zaak_identificatie": task.zaak_identificatie,
        }
        if existing_item := existing_uuid_mapping.get(task.uuid):
            if existing_item.type_data != type_data:
                existing_item.type_data = type_data
                update_data.append(existing_item)
            continue

        create_data.append(
            FeedItemData(
                user=user,
                type=FeedItemType.external_task,
                ref_uuid=task.uuid,
                action_required=True,
                type_data=type_data,
            )
        )

    # TODO we could maybe use `bulk_create` once we upgraded to Django 4.x
    FeedItemData.objects.bulk_update(update_data, ["type_data"], batch_size=100)
    FeedItemData.objects.bulk_create(create_data)

    # Mark all tasks with UUIDs not occurring in the fetched results as completed
    completed_uuids = existing_uuids - {task.uuid for task in openstaande_taken}
    FeedItemData.objects.filter(
        type=FeedItemType.external_task, user=user, ref_uuid__in=completed_uuids
    ).mark_completed()


def update_user_tasks(user: User):
    if user.login_type == LoginTypeChoices.digid:
        if client := build_forms_client():
            try:
                tasks = client.fetch_open_tasks(user.bsn)
            except (RequestException, ClientError):
                logger.exception("Something went wrong while fetching open tasks")
            else:
                update_external_task_items(user, tasks)


register_item_adapter(OpenTaskFeedItem, FeedItemType.external_task)
