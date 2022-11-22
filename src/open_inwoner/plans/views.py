from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.urls.base import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.forms import ActionListForm, DocumentForm
from open_inwoner.accounts.views.actions import (
    ActionCreateView,
    ActionDeleteView,
    ActionUpdateView,
    BaseActionFilter,
)
from open_inwoner.utils.logentry import get_change_message
from open_inwoner.utils.mixins import ExportMixin
from open_inwoner.utils.views import LogMixin

from .forms import PlanForm, PlanGoalForm
from .models import Plan


class PlanListView(LoginRequiredMixin, BaseBreadcrumbMixin, ListView):
    template_name = "pages/plans/list.html"
    model = Plan

    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerkingsplannen"), reverse("plans:plan_list")),
        ]

    def get_queryset(self):
        return (
            Plan.objects.connected(self.request.user)
            .select_related("created_by")
            .prefetch_related("contacts")
        )


class PlanDetailView(
    LoginRequiredMixin, BaseBreadcrumbMixin, BaseActionFilter, DetailView
):
    template_name = "pages/plans/detail.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    breadcrumb_use_pk = False

    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerkingsplannen"), reverse("plans:plan_list")),
            (self.get_object().title, reverse("plans:plan_detail", kwargs=self.kwargs)),
        ]

    def get_queryset(self):
        return (
            Plan.objects.connected(self.request.user)
            .select_related("created_by")
            .prefetch_related("contacts")
        )

    def get_context_data(self, **kwargs):
        actions = self.object.actions.visible()
        context = super().get_context_data(**kwargs)
        context["contact_users"] = self.object.get_other_users(self.request.user)
        context["is_creator"] = self.request.user == self.object.created_by
        context["anchors"] = [
            ("#title", self.object.title),
            ("#goals", _("Doelen")),
            ("#files", _("Bestanden")),
            ("#actions", _("Acties")),
        ]
        context["action_form"] = ActionListForm(
            data=self.request.GET, users=actions.values_list("is_for_id", flat=True)
        )
        context["actions"] = self.get_actions(actions)
        return context


class PlanCreateView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, CreateView):
    template_name = "pages/plans/create.html"
    model = Plan
    form_class = PlanForm

    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerkingsplannen"), reverse("plans:plan_list")),
            (_("Maak samenwerkingsplan aan"), reverse("plans:plan_create")),
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(self.request.user)

        self.log_addition(self.object, _("plan was created"))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanEditView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, UpdateView):
    template_name = "pages/plans/edit.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = PlanForm

    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerkingsplannen"), reverse("plans:plan_list")),
            (self.get_object().title, reverse("plans:plan_detail", kwargs=self.kwargs)),
            (_("Bewerken"), reverse("plans:plan_edit", kwargs=self.kwargs)),
        ]

    def get_queryset(self):
        return (
            super(PlanEditView, self)
            .get_queryset()
            .filter(created_by=self.request.user)
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(self.request.user)

        self.log_change(self.object, _("plan was modified"))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanGoalEditView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, UpdateView):
    template_name = "pages/plans/goal_edit.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = PlanGoalForm
    breadcrumb_use_pk = False

    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerkingsplannen"), reverse("plans:plan_list")),
            (self.get_object().title, reverse("plans:plan_detail", kwargs=self.kwargs)),
            (_("Doel bewerken"), reverse("plans:plan_edit_goal", kwargs=self.kwargs)),
        ]

    def get_queryset(self):
        return Plan.objects.connected(self.request.user)

    def form_valid(self, form):
        self.object = form.save()

        self.log_change(self.object, _("plan goal was modified"))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanFileUploadView(LogMixin, LoginRequiredMixin, BaseBreadcrumbMixin, UpdateView):
    template_name = "pages/plans/file.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = DocumentForm

    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerkingsplannen"), reverse("plans:plan_list")),
            (self.get_object().title, reverse("plans:plan_detail", kwargs=self.kwargs)),
            (
                _("Nieuw bestand uploaden"),
                reverse("plans:plan_add_file", kwargs=self.kwargs),
            ),
        ]

    def get_queryset(self):
        return Plan.objects.connected(self.request.user)

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": None})
        return kwargs

    def form_valid(self, form):
        object = self.get_object()
        form.save(self.request.user, plan=self.object)

        self.log_user_action(object, _("file was uploaded"))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanActionCreateView(ActionCreateView):
    model = Plan

    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerkingsplannen"), reverse("plans:plan_list")),
            (self.get_object().title, reverse("plans:plan_detail", kwargs=self.kwargs)),
            (
                _("Maak actie aan"),
                reverse("plans:plan_action_create", kwargs=self.kwargs),
            ),
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(plan=self.get_object())
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        context["plan"] = plan
        context["object"] = plan
        return context

    def get_object(self):
        try:
            return Plan.objects.connected(self.request.user).get(
                uuid=self.kwargs.get("uuid")
            )
        except ObjectDoesNotExist as e:
            raise Http404

    def form_valid(self, form):
        self.object = self.get_object()
        self.action = form.save(self.request.user)

        self.log_addition(
            self.action,
            _("action was created via plan"),
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanActionEditView(ActionUpdateView):
    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerkingsplannen"), reverse("plans:plan_list")),
            (
                self.get_plan().title,
                reverse("plans:plan_detail", kwargs={"uuid": self.get_plan().uuid}),
            ),
            (
                _("Bewerk {}").format(self.object.name),
                reverse("plans:plan_action_edit", kwargs=self.kwargs),
            ),
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(plan=self.get_plan())
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_plan()
        context["plan"] = plan
        context["object"] = plan
        return context

    def get_plan(self):
        try:
            return Plan.objects.connected(self.request.user).get(
                uuid=self.kwargs.get("plan_uuid")
            )
        except ObjectDoesNotExist as e:
            raise Http404

    def form_valid(self, form):
        self.object = self.get_plan()
        self.action = form.save(self.request.user)

        # log and notify if the action was changed
        if form.changed_data:
            # log
            changed_message = get_change_message(form=form)
            self.log_change(self.action, changed_message)

            # notify
            other_users = self.object.get_other_users(user=self.request.user)
            if other_users.count():
                self.action.send(
                    plan=self.object,
                    message=changed_message,
                    receivers=other_users,
                    request=self.request,
                )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanActionDeleteView(ActionDeleteView):
    # TODO do we need to do something depending on related users? (see the view above)

    def get_plan(self):
        try:
            return Plan.objects.connected(self.request.user).get(
                uuid=self.kwargs.get("plan_uuid")
            )
        except ObjectDoesNotExist as e:
            raise Http404

    def get_success_url(self) -> str:
        return self.get_plan().get_absolute_url()


class PlanExportView(LogMixin, LoginRequiredMixin, ExportMixin, DetailView):
    template_name = "export/plans/plan_export.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return Plan.objects.connected(self.request.user).prefetch_related("actions")
