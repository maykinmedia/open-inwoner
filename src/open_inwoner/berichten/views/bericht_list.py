import logging

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.berichten.services import BerichtenService
from open_inwoner.berichten.views.mixins import RequireBsnMixin
from open_inwoner.utils.views import CommonPageMixin

logger = logging.getLogger(__name__)


class BerichtListView(
    CommonPageMixin,
    BaseBreadcrumbMixin,
    RequireBsnMixin,
    TemplateView,
):

    template_name = "pages/berichten/list.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn berichten"), reverse("berichten:list")),
        ]

    def page_title(self):
        return _("Mijn berichten")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = BerichtenService()
        bsn = self.request.user.bsn if hasattr(self.request.user, "bsn") else None
        context["berichten"] = service.fetch_berichten_for_bsn(bsn) if bsn else []

        return context
