from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from view_breadcrumbs import (
    CreateBreadcrumbMixin,
    DetailBreadcrumbMixin,
    ListBreadcrumbMixin,
)

from open_inwoner.accounts.forms import ActionListForm
from open_inwoner.accounts.models import Document
from open_inwoner.accounts.views.actions import ActionCreateView, BaseActionFilter

from .forms import PlanForm, PlanGoalForm
from .models import Plan


class FileForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("file", "name")

    def save(self, user, plan=None, commit=True):
        self.instance.owner = user
        if plan:
            self.instance.plan = plan

        return super().save(commit=commit)


class PlanListView(LoginRequiredMixin, ListBreadcrumbMixin, ListView):
    template_name = "pages/plans/list.html"
    model = Plan

    def get_queryset(self):
        return Plan.objects.connected(self.request.user)


class PlanDetailView(
    LoginRequiredMixin, DetailBreadcrumbMixin, BaseActionFilter, DetailView
):
    template_name = "pages/plans/detail.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    breadcrumb_use_pk = False

    def get_queryset(self):
        return Plan.objects.connected(self.request.user)

    def get_context_data(self, **kwargs):
        actions = self.object.actions.all()
        context = super().get_context_data(**kwargs)
        context["action_form"] = ActionListForm(
            data=self.request.GET, users=actions.values_list("created_by_id", flat=True)
        )
        context["actions"] = self.get_actions(actions)
        return context


class PlanCreateView(LoginRequiredMixin, CreateBreadcrumbMixin, CreateView):
    template_name = "pages/plans/create.html"
    model = Plan
    form_class = PlanForm

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanGoalEditView(LoginRequiredMixin, UpdateView):
    template_name = "pages/plans/create.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = PlanGoalForm
    breadcrumb_use_pk = False

    def get_queryset(self):
        return Plan.objects.connected(self.request.user)

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanFileUploadView(LoginRequiredMixin, UpdateView):
    template_name = "pages/plans/file.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = FileForm

    def get_queryset(self):
        return Plan.objects.connected(self.request.user)

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": None})
        return kwargs

    def form_valid(self, form):
        form.save(self.request.user, plan=self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanActionCreateView(ActionCreateView):
    model = Plan

    def get_object(self):
        return Plan.objects.connected(self.request.user).get(
            uuid=self.kwargs.get("uuid")
        )

    def form_valid(self, form):
        self.object = self.get_object()
        form.save(self.request.user, plan=self.object)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()
