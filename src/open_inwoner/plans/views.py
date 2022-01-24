from django import forms
from django.http.response import HttpResponseRedirect
from django.urls.base import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from view_breadcrumbs import (
    CreateBreadcrumbMixin,
    DetailBreadcrumbMixin,
    ListBreadcrumbMixin,
    UpdateBreadcrumbMixin,
)

from open_inwoner.accounts.choices import EmptyStatusChoices
from open_inwoner.accounts.forms import ActionListForm
from open_inwoner.accounts.models import Action, Document
from open_inwoner.utils.views import CustomDetailBreadcrumbMixin

from .forms import PlanForm, PlanGoalForm
from .models import Plan


class ActionListForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = ("status", "end_date", "created_by")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["created_by"].required = False
        self.fields["end_date"].required = False
        self.fields["status"].required = False
        self.fields["status"].initial = ""
        self.fields["status"].choices = EmptyStatusChoices.choices


class FileForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ("file", "name")

    def save(self, user, plan=None, commit=True):
        self.instance.owner = user
        if plan:
            self.instance.plan = plan

        return super().save(commit=commit)


class PlanListView(ListBreadcrumbMixin, ListView):
    template_name = "pages/plans/list.html"
    model = Plan

    def get_queryset(self):
        return Plan.objects.filter(created_by=self.request.user)


class PlanDetailView(DetailBreadcrumbMixin, DetailView):
    template_name = "pages/plans/detail.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    breadcrumb_use_pk = False

    def get_queryset(self):
        return Plan.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_form"] = ActionListForm(data=self.request.GET)
        return context


class PlanCreateView(CreateBreadcrumbMixin, CreateView):
    template_name = "pages/plans/create.html"
    model = Plan
    form_class = PlanForm
    success_url = reverse_lazy("plans:plan_list")

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanGoalEditView(UpdateView):
    template_name = "pages/plans/create.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = PlanGoalForm
    breadcrumb_use_pk = False

    def form_valid(self, form):
        self.object = form.save(self.request.user)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanFileUploadView(UpdateView):
    template_name = "pages/plans/file.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = FileForm
    success_url = reverse_lazy("plans:plan_list")

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
