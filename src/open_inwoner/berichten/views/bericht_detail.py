import logging

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.berichten.services import BerichtenService
from open_inwoner.utils.views import CommonPageMixin

logger = logging.getLogger(__name__)


class BerichtDetailView(CommonPageMixin, BaseBreadcrumbMixin, TemplateView):

    template_name = "pages/berichten/detail.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn berichten"), reverse("berichten:list")),
            (_("Bericht"), reverse("berichten:detail", kwargs=self.kwargs)),
        ]

    def page_title(self):
        return _("Mijn berichten")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = BerichtenService()
        bericht = service.fetch_bericht(self.kwargs["object_uuid"])
        context["bericht"] = bericht
        if not bericht.geopend:
            service.update_object(self.kwargs["object_uuid"], {"geopend": True})

        return context
