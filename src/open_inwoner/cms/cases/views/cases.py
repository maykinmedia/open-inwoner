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
    ZaakWithApiGroupZaakTypeResolved,
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
    zaken: Iterable[ZaakWithApiGroupZaakTypeResolved],
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
        search = self.request.GET.get("search", "")
        page = self.request.GET.get(InnerCaseListView.page_kwarg, "")

        f_url = furl(reverse("cases:cases_content"))
        f_url.args.addlist("status", statuses)
        if search:
            f_url.args["search"] = search
        # The pagination links push `page` into the location bar, so reloading or
        # sharing the URL has to load that same page in the inner view.
        if page:
            f_url.args[InnerCaseListView.page_kwarg] = page

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

    # When the backend is slow and the cache is cold, part of the case list is
    # dropped by the per-stage timeouts. Timed-out fetches are not cancelled, so
    # they keep running and populate the cache; retrying therefore converges.
    MAX_AUTO_RETRIES = 2
    AUTO_RETRY_DELAY_S = 5
    RETRY_PARAM = "retry"

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

        try:
            page_number = int(self.request.GET.get(self.page_kwarg, 1))
        except (TypeError, ValueError):
            page_number = 1

        all_visible_zaken = []
        formulieren = []
        partial_results = False

        search = self.request.GET.get("search", "").strip()
        if search and self.request.user.is_authenticated and user_identification:
            search_result = case_service.search_zaken(
                user_identification, zaak_identificatie=search
            )
            all_visible_zaken = search_result.zaken
            partial_results = search_result.is_incomplete
        else:
            formulieren_result = case_service.get_formulieren(user_identification)
            formulieren: Sequence[UniformCase] = formulieren_result.formulieren

            visible_result = case_service.get_visible_zaken(user_identification)
            all_visible_zaken = visible_result.zaken

            partial_results = (
                formulieren_result.timed_out or visible_result.is_incomplete
            )

        if config.zaken_filter_enabled:
            case_status_frequencies = _get_zaak_status_frequencies(
                zaken=all_visible_zaken,
                formulieren=formulieren,
            )
            context["status_freqs"] = [
                (status.value, frequency)
                for status, frequency in case_status_frequencies.items()
            ]

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

            if statuses:
                formulieren = (
                    formulieren if CaseFilterFormOption.FORMULIER in statuses else []
                )
                all_visible_zaken = [
                    zaak
                    for zaak in all_visible_zaken
                    if _get_zaak_filter_status(zaak.zaak) in statuses
                ]

        # Formulieren fill the first slots; zaken follow.
        # max(0, ...) prevents negative indices when the page falls entirely within
        # the formulieren block, in which case zaak_start == zaak_end == 0 and
        # all_visible_zaken[0:0] == [] so no zaken are resolved.
        formulieren_count = len(formulieren)
        combined_start = (page_number - 1) * self.paginate_by
        combined_end = page_number * self.paginate_by
        formulieren_page = formulieren[combined_start:combined_end]
        zaak_start = max(0, combined_start - formulieren_count)
        zaak_end = max(0, combined_end - formulieren_count)
        resolved_result = case_service.fully_resolve_zaken(
            all_visible_zaken[zaak_start:zaak_end]
        )
        zaak_page = resolved_result.zaken
        partial_results = partial_results or resolved_result.is_incomplete

        page_items = [*formulieren_page, *zaak_page]
        combined_total = formulieren_count + len(all_visible_zaken)

        paginator_dict = self.paginate_preloaded(
            page_items, combined_total, page_number, self.paginate_by
        )
        zaken_dicts = [case.process_data() for case in paginator_dict["object_list"]]

        context["zaken"] = zaken_dicts
        context.update(paginator_dict)
        context["hxget"] = reverse("cases:cases_content")
        context["title_text"] = config.title_text
        context["zaak_identificatie_label"] = config.zaak_identificatie_label

        context.update(self._get_retry_context(partial_results))

        self.log_case_list_accessed(zaken_dicts)

        return context

    def _get_retry_context(self, partial_results: bool) -> dict:
        """Build the context for the partial-results banner and auto-retry.

        While retries remain, the template renders an element that re-requests
        the inner view with an incremented counter. Once they are exhausted the
        user gets a manual retry link back to the outer page, which starts a
        fresh cycle.
        """
        context: dict = {"partial_results": partial_results}

        if not partial_results:
            return context

        try:
            retry_count = int(self.request.GET.get(self.RETRY_PARAM, 0))
        except (TypeError, ValueError):
            retry_count = 0
        retry_count = max(0, min(retry_count, self.MAX_AUTO_RETRIES))

        # Preserves filters and search; note this also carries `page`, so a retry
        # re-renders the page the user is on.
        params = self.request.GET.copy()

        if retry_count < self.MAX_AUTO_RETRIES:
            params[self.RETRY_PARAM] = retry_count + 1
            context["auto_retry_url"] = (
                f"{reverse('cases:cases_content')}?{params.urlencode()}"
            )
            context["auto_retry_delay"] = self.AUTO_RETRY_DELAY_S
        else:
            params.pop(self.RETRY_PARAM, None)
            query = params.urlencode()
            context["manual_retry_url"] = (
                f"{reverse('cases:index')}?{query}" if query else reverse("cases:index")
            )

        return context
