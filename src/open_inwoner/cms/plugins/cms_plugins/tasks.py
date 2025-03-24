import logging
from dataclasses import asdict

from django.utils import formats
from django.utils.translation import gettext as _

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from objectsapiclient.models import Configuration

from ..api_models import Object, ObjecttypeTaak
from ..models import TasksConfig

logger = logging.getLogger(__name__)


@plugin_pool.register_plugin
class TasksPlugin(CMSPluginBase):
    """
    Uses the Objects API to retrieve and show tasks according to the MijnTaken Objecttypes schema
    Reuses the UserFeedPlugin template
    """

    model = TasksConfig
    name = _("Task list Plugin")
    render_template = "cms/plugins/tasks/tasks.html"
    cache = False

    def render(self, context, instance, placeholder) -> dict[str, str]:
        request = context["request"]
        context["instance"] = instance
        context["tasks"] = []

        if not request.user.is_authenticated or not (bsn := request.user.bsn):
            return context

        task_objects = self.get_tasks_by_bsn(user_bsn=bsn)

        task_dicts = []
        for task in task_objects:
            task_data = {
                "titel": task.titel,
                "soort": task.soort,
                "status": task.status,
                "verloopdatum": formats.date_format(
                    task.verloopdatum,
                    format="DATETIME_FORMAT",
                    use_l10n=True,
                ),
                "identificatie": task.identificatie.value,
                "koppeling": task.koppeling,
                "verwerker_taak_id": str(task.verwerker_taak_id),
                "eigenaar": task.eigenaar,
            }

            match task.soort:
                case "url":
                    task_data["task_url"] = str(task.url.uri)
                case _:
                    raise ValueError(
                        "Unsupported type for externe taak: %s", task.soort
                    )

            task_dicts.append(task_data)

        context["tasks"] = task_dicts

        return context

    def get_tasks(self) -> list[ObjecttypeTaak]:
        """
        Retrieve `object`s from the Objects API and extract `taken`

        Pydantic models are used to validate that objects and taken data have the expected shape

        OIP currently only supports externe klanttaken of type `URL Taak`
        """
        objects_api_client = Configuration.get_solo().client

        objects = [
            Object(**asdict(obj))
            for obj in objects_api_client.get_objects(
                object_type_uuid=self.model.object_type
            )
        ]

        return [
            ObjecttypeTaak(**obj.record.data)
            for obj in objects
            if obj.record.data["soort"] == "url"
        ]

    def get_tasks_by_bsn(self, user_bsn) -> list[ObjecttypeTaak]:
        return [
            task
            for task in self.get_tasks()
            if task.identificatie.type == "bsn" and task.identificatie.value == user_bsn
        ]
