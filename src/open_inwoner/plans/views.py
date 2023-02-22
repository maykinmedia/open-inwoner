from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.urls.base import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.accounts.choices import ContactTypeChoices
from open_inwoner.accounts.forms import ActionListForm, DocumentForm
from open_inwoner.accounts.models import User
from open_inwoner.accounts.views.actions import (
    ActionCreateView,
    ActionDeleteView,
    ActionUpdateStatusTagView,
    ActionUpdateView,
    BaseActionFilter,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.logentry import get_change_message
from open_inwoner.utils.mixins import ExportMixin
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from .forms import PlanForm, PlanGoalForm, PlanListFilterForm
from .models import Plan


class PlansEnabledMixin:
    def dispatch(self, request, *args, **kwargs):
        config = SiteConfiguration.get_solo()
        if not config.show_plans:
            raise Http404("plans not enabled")
        return super().dispatch(request, *args, **kwargs)


class BasePlanFilter:
    """
    This will filter the plans according to the user's selection or query.
    """

    def get_filtered_plans(self, plans, available_contacts):
        plan_contacts = self.request.GET.get("plan_contacts")
        status = self.request.GET.get("status")
        query = self.request.GET.get("query")
        today = date.today()

        if not (plan_contacts or status or query):
            return plans

        if plan_contacts:
            plans = plans.filter(plan_contacts__uuid=plan_contacts)
        if status:
            if status == "open":
                plans = plans.filter(end_date__gt=today)
            elif status == "closed":
                plans = plans.filter(end_date__lte=today)
        if query:
            available_contacts = available_contacts.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )
            plans = plans.filter(
                Q(title__icontains=query) | Q(plan_contacts__in=available_contacts)
            )

        return plans.distinct()


class PlanListView(
    PlansEnabledMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    BasePlanFilter,
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
        return (
            Plan.objects.connected(self.request.user)
            .prefetch_related("plan_contacts")
            .order_by("end_date")
        )

    def get_available_contacts_for_filtering(self, plans):
        """
        Return all available contacts for filtering for all the plans.
        """
        user_contacts_qs = []
        for plan in plans:
            user_contacts_qs.append(plan.get_other_users(user=self.request.user))

        available_contacts = User.objects.none()
        for qs in user_contacts_qs:
            available_contacts |= qs

        return available_contacts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        initial_qs = self.get_queryset()
        plans = {"extended_plans": False}

        # render the extended plan list view when a begeleider is logged in
        if user.contact_type == ContactTypeChoices.begeleider:
            plans["extended_plans"] = True
            available_contacts = self.get_available_contacts_for_filtering(initial_qs)

            filtered_plans = self.get_filtered_plans(initial_qs, available_contacts)

            # sort the filtered plans based on if they are open or closed
            open_plans = filtered_plans.filter(end_date__gt=date.today())
            closed_plans = filtered_plans.filter(end_date__lte=date.today()).order_by(
                "-end_date"
            )
            sorted_plans = list(open_plans) + list(closed_plans)

            # paginate results
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                sorted_plans, 10
            )

            # instantiate filter form
            context["plan_filter_form"] = PlanListFilterForm(
                data=self.request.GET, available_contacts=available_contacts
            )

            # prepare plans for frontend
            temp_plans = {}
            for plan in queryset:
                temp_plans[plan] = plan.get_other_users_full_names(user=user)

            plans["plan_list"] = temp_plans
        else:
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                initial_qs, 10
            )
            plans["plan_list"] = queryset

        context["paginator"] = paginator
        context["page_obj"] = page
        context["is_paginated"] = is_paginated
        context["plans"] = plans
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
