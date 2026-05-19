import enum
from typing import Iterable, Sequence

from django.shortcuts import render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

import structlog
from furl import furl
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.htmx.mixins import RequiresHtmxMixin
from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.models import OpenZaakConfig
from open_inwoner.openzaak.services import (
    FormulierWithApiGroup,
    ZaakWithApiGroup,
    ZGWService,
)
from open_inwoner.openzaak.types import UniformCase
from open_inwoner.utils.mixins import PaginationMixin
from open_inwoner.utils.views import CommonPageMixin

from .mixins import CaseAccessMixin, CaseLogMixin, OuterCaseAccessMixin

logger = structlog.stdlib.get_logger(__name__)


class CaseFilterFormOption(enum.Enum):
    FORMULIER = _("Openstaande formulieren")
    ZAAK_OPEN = _("Lopende aanvragen")
    ZAAK_AFGEROND = _("Afgeronde aanvragen")


def _get_zaak_filter_status(zaak: Zaak) -> CaseFilterFormOption:
    if zaak.einddatum:
        return CaseFilterFormOption.ZAAK_AFGEROND
    return CaseFilterFormOption.ZAAK_OPEN


def _get_zaak_status_frequencies(
    zaken: Iterable[ZaakWithApiGroup],
    formulieren: Iterable[FormulierWithApiGroup],
) -> dict[CaseFilterFormOption, int]:
    zaak_statuses = [_get_zaak_filter_status(zaak.zaak) for zaak in zaken]
    zaak_statuses += [CaseFilterFormOption.FORMULIER for _ in formulieren]
    return {
        status: zaak_statuses.count(status) for status in list(CaseFilterFormOption)
    }


class OuterCaseListView(
    OuterCaseAccessMixin, CommonPageMixin, BaseBreadcrumbMixin, TemplateView
):
    """View on the case list while content is loaded via htmx"""

    template_name = "pages/cases/list_outer.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn zaken"), reverse("cases:index")),
        ]

    def page_title(self):
        return _("Mijn zaken")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        statuses = self.request.GET.getlist("status")

        f_url = furl(reverse("cases:cases_content"))
        f_url.args.addlist("status", statuses)

        context["hxget"] = f_url.url
        return context


class InnerCaseListView(
    RequiresHtmxMixin,
    CommonPageMixin,
    CaseAccessMixin,
    CaseLogMixin,
    PaginationMixin,
    TemplateView,
):
    template_name = "pages/cases/list_inner.html"
    paginate_by = 9

    def page_title(self):
        return _("Mijn zaken")

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception:
            logger.exception("Failed to fetch cases")
            return render(request, self.template_name, {"fetch_error": True})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = OpenZaakConfig.get_solo()
        user_identification = self.request.user.identification
        case_service = ZGWService()
        context["filter_form_enabled"] = config.zaken_filter_enabled

        # update ctx with formulieren and cases (possibly filtered)
        formulieren: Sequence[UniformCase] = case_service.get_formulieren(
            user_identification
        )
        preprocessed_zaken: Sequence[UniformCase] = case_service.get_zaken(
            user_identification
        )

        if config.zaken_filter_enabled:
            case_status_frequencies = _get_zaak_status_frequencies(
                zaken=preprocessed_zaken,
                formulieren=formulieren,
            )
            # Separate frequency data from statusname
            context["status_freqs"] = [
                (status.value, frequency)
                for status, frequency in case_status_frequencies.items()
            ]

            # Validate statuses are valid according to the options enum
            statuses: list[CaseFilterFormOption] = []
            for status in self.request.GET.getlist("status"):
                try:
                    statuses.append(CaseFilterFormOption(status))
                except ValueError:
                    logger.error(
                        "Invalid data for case filtering by",
                        data=self.request.GET,
                        user=self.request.user,
                    )

            # Actually filter the formulieren
            if statuses:
                formulieren = (
                    formulieren if CaseFilterFormOption.FORMULIER in statuses else []
                )
                preprocessed_zaken = [
                    zaak
                    for zaak in preprocessed_zaken
                    if _get_zaak_filter_status(zaak.zaak) in statuses
                ]

        paginator_dict = self.paginate_with_context([*formulieren, *preprocessed_zaken])
        zaken_dicts = [case.process_data() for case in paginator_dict["object_list"]]

        context["zaken"] = zaken_dicts
        context.update(paginator_dict)

        # other data
        context["hxget"] = reverse("cases:cases_content")
        context["title_text"] = config.title_text

        self.log_case_list_accessed(zaken_dicts)

        return context
