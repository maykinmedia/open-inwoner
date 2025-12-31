from enum import Enum
from typing import Generator, Type, TypedDict, assert_never, cast
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext as _, gettext_lazy

import structlog
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from furl import furl
from objectsapiclient.models import ObjectsAPIServiceConfiguration
from objectsapiclient.services import ObjectsAPIService
from pydantic import ValidationError
from requests import RequestException

from open_inwoner.mijn_aanvragen.api_models import OpenstaandeTaak
from open_inwoner.mijn_aanvragen.clients import build_forms_clients
from open_inwoner.mijn_aanvragen.cms.api_models import (
    ExternFormulierTaak,
    KoppelingProduct,
    KoppelingZaak,
    UrlTaak,
)
from open_inwoner.mijn_aanvragen.cms.models import TakenPluginConfig, ZakenPluginConfig
from open_inwoner.mijn_aanvragen.models import ZGWApiGroupConfig
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

    model = TakenPluginConfig
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

    def fetch_zgw_taken(self, bsn: str) -> list[OpenstaandeTaak]:
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
        try:
            service = ObjectsAPIService(ObjectsAPIServiceConfiguration.get_solo())
        except ImproperlyConfigured:
            logger.debug("Objects API service not configured, skipping external tasks")
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
            for obj in service.get_objects(object_type_uuid=object_type_uuid):
                record_data = obj.record.data
                if record_data is None:
                    logger.warning(
                        "Object has no data field",
                        object_uuid=obj.uuid,
                        object_type_uuid=object_type_uuid,
                    )
                    continue

                taak_data = cast(dict, record_data) | {"url": obj.url, "uuid": obj.uuid}
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


@plugin_pool.register_plugin
class CMSZakenPlugin(CMSPluginBase):
    model = ZakenPluginConfig
    name = gettext_lazy("Zaken Plugin")
    render_template = "cms/plugins/zaken/zaken.html"
    cache = False

    def render(self, context, instance, placeholder) -> dict:
        """
        Render the CMS Zaken Plugin

        This method prepares the initial container that will use HTMX to load
        zaken data asynchronously.
        """
        if not ZGWApiGroupConfig.objects.exists():
            return context

        user = context["request"].user
        if not user.is_authenticated or not user.is_bsn_user:
            return context

        # HTMX endpoint with num_zaken parameter
        f_url = furl(
            reverse("cms_plugins:zaken_content", kwargs={"plugin_id": instance.pk})
        )
        f_url.args["num_zaken"] = instance.num_zaken

        mijn_zaken_url = reverse("cases:index")

        context.update(
            {
                "show_zaken_plugin": True,
                "mijn_zaken_url": mijn_zaken_url,
                "plugin_title": instance.title,
                "hx_get_url": f_url.url,
            }
        )

        return context


__all__ = [
    "TasksPlugin",
    "CMSZakenPlugin",
]
