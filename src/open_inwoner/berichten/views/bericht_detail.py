import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.berichten.services import BerichtenService
from open_inwoner.utils.views import CommonPageMixin

logger = logging.getLogger(__name__)


class BerichtDetailView(
    CommonPageMixin, BaseBreadcrumbMixin, TemplateView, LoginRequiredMixin
):

    template_name = "pages/berichten/detail.html"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn berichten"), reverse("berichten:list")),
            (_("Overzicht"), reverse("berichten:detail", kwargs=self.kwargs)),
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


@login_required
def mark_bericht_as_unread(request, object_uuid):
    service = BerichtenService()
    service.update_object(object_uuid, {"geopend": False})
    return HttpResponseRedirect(reverse("berichten:list"))
