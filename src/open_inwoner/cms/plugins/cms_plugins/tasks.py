from enum import Enum
from typing import Generator, Type, TypedDict, assert_never
from urllib.parse import urlencode

from django.utils import formats
from django.utils.translation import gettext as _

import structlog
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from objectsapiclient.models import Configuration
from pydantic import ValidationError
from requests import RequestException

from open_inwoner.cms.plugins.api_models import (
    ExternFormulierTaak,
    KoppelingProduct,
    KoppelingZaak,
    UrlTaak,
)
from open_inwoner.cms.plugins.models import TasksConfig
from open_inwoner.openzaak.api_models import OpenTask
from open_inwoner.openzaak.clients import build_forms_clients
from open_inwoner.utils.api import ClientError

logger = structlog.stdlib.get_logger(__name__)


class TaskAPISource(Enum):
    ZGW_API = "ZGW API"
    OBJECTS_API = "Objects API"


class TaskData(TypedDict):
    # metadata for internal use
    api_source: TaskAPISource

    soort: str
    titel: str
    status: str
    verloopdatum: str
    koppeling: KoppelingProduct | KoppelingZaak | None
    eigenaar: str
    verwerker_taak_id: str
    taak_url: str


@plugin_pool.register_plugin
class TasksPlugin(CMSPluginBase):
    """
    Fetches and combines `openstaande taken` form ZGW API's and `externe taken`
    from Objects API.

    Note:
        Objects returned by the eSuite have fewer fields than those
        returned by the Objects API. For consistency, we use the same `TypedDict`
        for validation with empty defaults for the eSuite taken.
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

        task_dicts = []

        # fetch "openstaande taken" from ZGW API's
        zgw_taken = self.fetch_zgw_taken(bsn=bsn)
        task_dicts.extend(
            TaskData(
                api_source=TaskAPISource.ZGW_API.value,
                task_url=taak.formulier_link,
                status="open",
                titel=taak.naam,
                soort="",
                verloopdatum="",
                koppeling=None,
                eigenaar="",
                verwerker_taak_id="",
            )
            for taak in zgw_taken
        )

        # fetch externe taken from Objects API
        task_objects = self.get_tasks_by_bsn(instance, user_bsn=bsn)
        for task in task_objects:
            # determine task_url based on type
            match task:
                case ExternFormulierTaak():
                    base_url = task.portaalformulier.formulier.value
                    param = {"initial_data_reference": task.uuid}
                    task_url = f"{base_url}?{urlencode(param)}"
                case UrlTaak():
                    task_url = str(task.task_url.uri)
                case _:
                    assert_never(task)

            task_data = TaskData(
                api_source=TaskAPISource.OBJECTS_API.value,
                soort=task.soort,
                titel=task.titel,
                status=task.status,
                verloopdatum=formats.date_format(
                    task.verloopdatum if task.verloopdatum is not None else "",
                    format="DATETIME_FORMAT",
                    use_l10n=True,
                ),
                koppeling=task.koppeling,
                verwerker_taak_id=str(task.verwerker_taak_id),
                eigenaar=task.eigenaar,
                task_url=task_url,
            )

            task_dicts.append(task_data)

        context["tasks"] = task_dicts

        return context

    def fetch_zgw_taken(self, bsn: str) -> list[OpenTask]:
        """
        Fetch `openstaande taken` from ZGW API's
        """
        zgw_taken = []
        for zgw_client in build_forms_clients():
            try:
                taken = zgw_client.fetch_open_tasks(bsn=bsn)
            except (RequestException, ClientError):
                logger.exception(
                    "Error fetching 'openstaande taken' from ZGW API",
                    zgw_client=zgw_client,
                )
            else:
                zgw_taken.extend(taken)
        return zgw_taken

    def get_tasks(
        self, instance
    ) -> Generator[ExternFormulierTaak | UrlTaak, None, None]:
        """
        Fetch `externe taken` from Objects API
        """
        objects_api_client = Configuration.get_solo().client

        if objects_api_client is None:
            return

        factory_map: dict[str, Type[ExternFormulierTaak | UrlTaak]] = {}
        if instance.object_type_generieke_dienstverlening:
            factory_map[instance.object_type_generieke_dienstverlening] = (
                ExternFormulierTaak
            )
        # legacy type `UrlTaak`
        if instance.object_type_dimpact:
            factory_map[instance.object_type_dimpact] = UrlTaak

        for object_type_uuid, obj_factory in factory_map.items():
            for obj in objects_api_client.get_objects(
                object_type_uuid=object_type_uuid
            ):
                taak_data = obj.record["data"] | {"url": obj.url, "uuid": obj.uuid}
                try:
                    yield obj_factory.validate(taak_data)
                except ValidationError:
                    logger.exception(
                        "Invalid externe taak",
                        object_type_uuid=object_type_uuid,
                    )

    def get_tasks_by_bsn(
        self, instance, user_bsn
    ) -> Generator[ExternFormulierTaak | UrlTaak, None, None]:
        tasks = self.get_tasks(instance)

        for task in tasks:
            match task:
                case ExternFormulierTaak():
                    if (
                        task.betrokkene.source == "digid"
                        and task.betrokkene.authorizee.legal_subject.identifier
                        == user_bsn
                    ):
                        yield task
                case UrlTaak():
                    if (
                        task.identificatie.type == "bsn"
                        and task.identificatie.value == user_bsn
                    ):
                        yield task
                case _:
                    assert_never(task)
