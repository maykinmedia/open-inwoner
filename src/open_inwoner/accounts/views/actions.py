from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView
from django.views.generic.edit import UpdateView

from view_breadcrumbs import BaseBreadcrumbMixin

from ..forms import ActionForm
from ..models import Action


class ActionListView(LoginRequiredMixin, BaseBreadcrumbMixin, ListView):
    template_name = "pages/profile/actions/list.html"
    model = Action
    paginate_by = 10

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn acties"), reverse("accounts:action_list")),
        ]

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)


class ActionUpdateView(LoginRequiredMixin, BaseBreadcrumbMixin, UpdateView):
    template_name = "pages/profile/actions/edit.html"
    model = Action
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = ActionForm
    success_url = reverse_lazy("accounts:action_list")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn acties"), reverse("accounts:action_list")),
            (
                _("Bewerk {}").format(self.object.name),
                reverse("accounts:action_edit", kwargs=self.kwargs),
            ),
        ]

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(created_by=self.request.user)

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())


class ActionCreateView(LoginRequiredMixin, BaseBreadcrumbMixin, CreateView):
    template_name = "pages/profile/actions/edit.html"
    model = Action
    form_class = ActionForm
    success_url = reverse_lazy("accounts:action_list")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("accounts:my_profile")),
            (_("Mijn acties"), reverse("accounts:action_list")),
            (
                _("Maak actie aan"),
                reverse("accounts:action_create", kwargs=self.kwargs),
            ),
        ]

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())
