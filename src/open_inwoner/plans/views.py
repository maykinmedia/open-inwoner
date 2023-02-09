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
    ActionUpdateStatusTagView,
    ActionUpdateView,
    BaseActionFilter,
)
from open_inwoner.accounts.choices import ContactTypeChoices
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.logentry import get_change_message
from open_inwoner.utils.mixins import ExportMixin
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from .forms import PlanForm, PlanGoalForm
from .models import Plan


class PlansEnabledMixin:
    def dispatch(self, request, *args, **kwargs):
        config = SiteConfiguration.get_solo()
        if not config.show_plans:
            raise Http404("plans not enabled")
        return super().dispatch(request, *args, **kwargs)


class PlanListView(
    PlansEnabledMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    ListView,
):
    template_name = "pages/plans/list.html"
    model = Plan
    paginate_by = 10

    @cached_property
    def crumbs(self):
        return [
            (_("Samenwerken"), reverse("plans:plan_list")),
        ]

    def get_queryset(self):
        return Plan.objects.connected(self.request.user).prefetch_related(
            "plan_contacts"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.contact_type == ContactTypeChoices.begeleider:
            plans = {}
            for plan in self.get_queryset():
                plans[plan] = plan.get_other_users_full_names(user=self.request.user)

            context["extended_plans"] = plans
        return context


class PlanDetailView(
    PlansEnabledMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    BaseActionFilter,
    DetailView,
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
        return Plan.objects.connected(self.request.user).prefetch_related(
            "plan_contacts"
        )

    def get_context_data(self, **kwargs):
        actions = self.object.actions.visible()
        obj = self.object
        user = self.request.user
        context = super().get_context_data(**kwargs)

        context["contact_users"] = obj.get_other_users(user)
        context["is_creator"] = user == obj.created_by
        context["anchors"] = [
            ("#title", obj.title),
            ("#goals", _("Doelen")),
            ("#files", _("Bestanden")),
            ("#actions", _("Acties")),
        ]
        context["action_form"] = ActionListForm(
            data=self.request.GET, users=actions.values_list("is_for_id", flat=True)
        )
        context["actions"] = self.get_actions(actions)
        return context


class PlanCreateView(
    PlansEnabledMixin,
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    CreateView,
):
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

        # Add plan creator as a plan_contact as well
        self.object.plan_contacts.add(self.object.created_by)

        self.log_addition(self.object, _("plan was created"))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class PlanEditView(
    PlansEnabledMixin,
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    UpdateView,
):
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


class PlanGoalEditView(
    PlansEnabledMixin,
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    UpdateView,
):
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


class PlanFileUploadView(
    PlansEnabledMixin,
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    UpdateView,
):
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


class PlanActionCreateView(PlansEnabledMixin, ActionCreateView):
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


class PlanActionEditView(PlansEnabledMixin, ActionUpdateView):
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


class PlanActionEditStatusTagView(PlansEnabledMixin, ActionUpdateStatusTagView):
    def get_plan(self):
        try:
            return Plan.objects.connected(self.request.user).get(
                uuid=self.kwargs.get("plan_uuid")
            )
        except ObjectDoesNotExist as e:
            raise Http404

    def get_template_tag_args(self, context):
        args = super().get_template_tag_args(context)
        args["plan"] = self.get_plan()
        return args


class PlanActionDeleteView(PlansEnabledMixin, ActionDeleteView):
    def get_plan(self):
        try:
            return Plan.objects.connected(self.request.user).get(
                uuid=self.kwargs.get("plan_uuid")
            )
        except ObjectDoesNotExist as e:
            raise Http404

    def get_success_url(self) -> str:
        return self.get_plan().get_absolute_url()

    def on_delete_action(self, action):
        super().on_delete_action(action)

        # notify
        plan = self.get_plan()
        other_users = plan.get_other_users(user=self.request.user)
        if other_users.count():
            action.send(
                plan=plan,
                message=_("Actie '{action}' is verwijdered.").format(action=action),
                receivers=other_users,
                request=self.request,
            )


class PlanExportView(
    PlansEnabledMixin, LogMixin, LoginRequiredMixin, ExportMixin, DetailView
):
    template_name = "export/plans/plan_export.html"
    model = Plan
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return Plan.objects.connected(self.request.user).prefetch_related("actions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()

        context["plan_contacts"] = plan.get_other_users_full_names(self.request.user)
        return context
