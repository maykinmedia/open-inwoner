from typing import Sequence

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

import structlog
from furl import furl

from open_inwoner.cms.cases.views.mixins import CaseLogMixin
from open_inwoner.cms.plugins.models import CMSZakenPluginConfig
from open_inwoner.cms.plugins.models.zaken import MAX_CASES_DEFAULT, MIN_CASES
from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.constants import TypeAanvraag
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import ZGWService
from open_inwoner.openzaak.types import UniformCase

logger = structlog.stdlib.get_logger(__name__)


class ZakenPluginContentView(RequiresHtmxMixin, CaseLogMixin, View):
    """
    HTMX endpoint that fetches and returns content for the `CMSZakenPlugin`.
    """

    def _get_detail_label(self, zaak: dict, zaak_identificatie_label: str) -> str:
        """
        Generate the detail label to display under the card title.
        """

        is_formulier = zaak.get("type_aanvraag") == TypeAanvraag.FORMULIER.value
        identification = zaak.get("identification", "")

        if is_formulier or not identification:
            return ""

        return f"{zaak_identificatie_label} {identification}"

    def get(self, request: HttpRequest, plugin_id: int) -> HttpResponse:
        user_identification = (
            request.user.identification if request.user.is_authenticated else None
        )
        case_service = ZGWService()

        # Get plugin instance for title
        try:
            plugin_instance = CMSZakenPluginConfig.objects.get(pk=plugin_id)
            plugin_title = plugin_instance.title
        except CMSZakenPluginConfig.DoesNotExist:
            logger.warning("Plugin instance not found", plugin_id=plugin_id)
            plugin_title = _("Mijn Zaken")

        # determine no. of zaken to be displayed
        num_zaken = request.GET.get("num_zaken", 0)
        try:
            num_zaken = int(num_zaken)
            if num_zaken < MIN_CASES or num_zaken > MAX_CASES_DEFAULT:
                logger.warning(
                    "Missing or invalid num_zaken value, using default",
                    num_zaken=num_zaken,
                )
                num_zaken = MAX_CASES_DEFAULT
        except (ValueError, TypeError) as exc:
            logger.warning(
                "Invalid num_zaken parameter, using default",
                value=num_zaken,
                error=str(exc),
            )
            num_zaken = MAX_CASES_DEFAULT

        # fetch zaken + formulieren
        # note: we count the retrieval as success of one part is successfully retrieved
        msg = None
        partial_error_msg = _(
            "We're experiencing technical difficulties. Some results may be missing from your cases."
        )
        try:
            formulieren_result = case_service.get_formulieren(user_identification)
        except Exception:
            logger.error("Failed to retrieve formulieren", user=request.user)
            formulieren: Sequence[UniformCase] | None = None
            msg = partial_error_msg
        else:
            formulieren = formulieren_result.formulieren
            if formulieren_result.timed_out:
                msg = partial_error_msg
        try:
            all_visible_zaken = case_service.get_visible_zaken(
                user_identification
            ).zaken
        except Exception:
            logger.error("Failed to retrieve zaken", user=request.user)
            all_visible_zaken = None

        if formulieren is None and all_visible_zaken is None:
            context = {
                "show_zaken_plugin": True,
                "zaken": [],
                "error_message": "We're experiencing technical difficulties showing your cases.",
                "plugin_title": plugin_title,
                "mijn_zaken_url": reverse("cases:index"),
            }
            return render(request, "cms/plugins/zaken/zaken.html", context)

        # Formulieren fill the first slots; only fully-resolve as many zaken as needed.
        formulieren_to_show = (formulieren or [])[:num_zaken]
        zaak_limit = max(0, num_zaken - len(formulieren_to_show))
        zaken_page = case_service.fully_resolve_zaken(
            (all_visible_zaken or [])[:zaak_limit]
        ).zaken
        zaken_dicts = [
            zaak.process_data() for zaak in [*formulieren_to_show, *zaken_page]
        ]
        self.log_case_list_accessed(zaken_dicts)

        openzaak_config = OpenZaakConfig.get_solo()

        # format data for web component
        cases_for_component = []
        for zaak in zaken_dicts:
            try:
                is_formulier = zaak.get("type_aanvraag") == TypeAanvraag.FORMULIER.value
                if is_formulier:
                    url = zaak.get("vervolg_link") or ""
                else:
                    url = furl(
                        reverse(
                            "cases:case_detail",
                            kwargs={
                                "object_id": zaak["uuid"],
                                "api_group_id": str(zaak["api_group"].id),
                            },
                        )
                    ).url
                case_data = {
                    "uuid": zaak["uuid"],
                    "url": url,
                    "identification": zaak.get("identification", ""),
                    "title": zaak.get("naam", zaak.get("description", "")),
                    "detail_label": self._get_detail_label(
                        zaak, openzaak_config.zaak_identificatie_label
                    ),
                }
            except (AttributeError, KeyError):
                logger.error(
                    "Failed to retrieve necessary attributes for zaak", zaak=zaak
                )
                msg = partial_error_msg
            else:
                cases_for_component.append(case_data)

        context = {
            "show_zaken_plugin": True,
            "zaken": cases_for_component,
            "error_message": msg,
            "plugin_title": plugin_title,
            "mijn_zaken_url": reverse("cases:index"),
        }

        return render(request, "cms/plugins/zaken/zaken.html", context)


zaken_plugin_content_view = ZakenPluginContentView.as_view()
