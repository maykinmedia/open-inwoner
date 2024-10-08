import logging

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.berichten.mock_data import MOCK_BERICHTEN
from open_inwoner.utils.views import CommonPageMixin

logger = logging.getLogger(__name__)


class BerichtListView(CommonPageMixin, BaseBreadcrumbMixin, TemplateView):

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
        context["berichten"] = MOCK_BERICHTEN
        return context
