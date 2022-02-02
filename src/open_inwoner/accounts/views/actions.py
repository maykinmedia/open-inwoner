from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView
from django.views.generic.edit import UpdateView

from view_breadcrumbs import BaseBreadcrumbMixin

from ..forms import ActionForm, ActionListForm
from ..models import Action


class BaseActionFilter:
    """
    For when in the template the action tag is used. This will filter the actions correctly.
    """

    def get_actions(self, actions):
        if self.request.GET.get("end_date"):
            end_date = datetime.strptime(
                self.request.GET.get("end_date"), "%d-%m-%Y"
            ).date()
            actions = actions.filter(end_date=end_date)
        if self.request.GET.get("created_by"):
            actions = actions.filter(created_by=self.request.GET.get("created_by"))
        if self.request.GET.get("status"):
            actions = actions.filter(status=self.request.GET.get("status"))
        return actions


class ActionListView(
    LoginRequiredMixin, BaseBreadcrumbMixin, BaseActionFilter, ListView
):
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
        return base_qs.filter(is_for=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_form"] = ActionListForm(
            data=self.request.GET, users=self.get_queryset()
        )
        context["actions"] = self.get_actions(self.get_queryset())
        return context


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
        return base_qs.filter(is_for=self.request.user)

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
