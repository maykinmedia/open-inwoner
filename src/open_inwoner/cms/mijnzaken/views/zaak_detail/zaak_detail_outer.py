import logging

from django.http import Http404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.openzaak.api_models import Zaak
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.utils.views import CommonPageMixin

from ..mixins import CaseAccessMixin, OuterCaseAccessMixin

logger = logging.getLogger(__name__)


class OuterCaseDetailView(
    OuterCaseAccessMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    CaseAccessMixin,
    TemplateView,
):
    template_name = "pages/cases/status_outer.html"
    case: Zaak | None = None

    @cached_property
    def crumbs(self):
        # case is retrieved via CaseAccessMixin
        if self.case:
            return [
                (_("Mijn zaken"), reverse("cases:index")),
                (
                    f"{self.case.description} - {_('Status')}",
                    reverse("cases:case_detail", kwargs=self.kwargs),
                ),
            ]
        return [
            (_("Mijn zaken"), reverse("cases:index")),
            (
                f"{_('Zaak')} - {_('Status')}",
                reverse("cases:case_detail", kwargs=self.kwargs),
            ),
        ]

    def page_title(self):
        if self.case:
            return f"{self.case.description} {self.case.identification} - {_('Status')}"
        else:
            return f"{_('Zaak')} - {_('Status')}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hxget"] = reverse("cases:case_detail_content", kwargs=self.kwargs)
        context["custom_anchors"] = True
        return context

    def get(self, request, *args, **kwargs):
        try:
            ZGWApiGroupConfig.objects.get(pk=self.kwargs["api_group_id"])
        except ZGWApiGroupConfig.DoesNotExist as exc:
            logger.exception("Non-existent ZGWApiGroupConfig passed")
            raise Http404 from exc

        return super().get(request, *args, **kwargs)
