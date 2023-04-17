from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http.response import Http404, HttpResponseRedirect
from django.urls.base import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import DeletionMixin, UpdateView

from privates.views import PrivateMediaView
from view_breadcrumbs import BaseBreadcrumbMixin

from open_inwoner.components.utils import RenderableTag
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.htmx.views import HtmxTemplateTagModelFormView
from open_inwoner.utils.logentry import get_verbose_change_message
from open_inwoner.utils.mixins import ExportMixin
from open_inwoner.utils.views import CommonPageMixin, LogMixin

from ..forms import ActionForm, ActionListForm
from ..models import Action


class ActionsEnabledMixin:
    def dispatch(self, request, *args, **kwargs):
        config = SiteConfiguration.get_solo()
        if not config.show_actions:
            raise Http404("actions not enabled")
        return super().dispatch(request, *args, **kwargs)


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
        if self.request.GET.get("is_for"):
            actions = actions.filter(is_for=self.request.GET.get("is_for"))
        if self.request.GET.get("status"):
            actions = actions.filter(status=self.request.GET.get("status"))
        return actions


class ActionListView(
    ActionsEnabledMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    BaseActionFilter,
    ListView,
):
    template_name = "pages/profile/actions/list.html"
    model = Action

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Mijn acties"), reverse("profile:action_list")),
        ]

    def get_queryset(self):
        base_qs = super().get_queryset()
        return (
            base_qs.visible().connected(user=self.request.user).select_related("is_for")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_form"] = ActionListForm(
            data=self.request.GET,
            users=self.get_queryset().values_list("is_for_id", flat=True),
        )

        actions = self.get_actions(self.get_queryset())
        paginator, page, queryset, is_paginated = self.paginate_queryset(actions, 10)
        context["paginator"] = paginator
        context["page_obj"] = page
        context["is_paginated"] = is_paginated
        context["actions"] = queryset
        return context


class ActionUpdateView(
    ActionsEnabledMixin,
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    UpdateView,
):
    template_name = "pages/profile/actions/edit.html"
    model = Action
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    form_class = ActionForm
    success_url = reverse_lazy("profile:action_list")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Mijn acties"), reverse("profile:action_list")),
            (
                _("Bewerk {}").format(self.object.name),
                reverse("profile:action_edit", kwargs=self.kwargs),
            ),
        ]

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.visible().connected(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(self.request.user)

        # log if the action was changed
        if form.changed_data:
            changed_message = get_verbose_change_message(form=form)
            self.log_change(self.object, changed_message)
        return HttpResponseRedirect(self.get_success_url())


class ActionUpdateStatusTagView(
    LogMixin, LoginRequiredMixin, HtmxTemplateTagModelFormView
):
    model = Action
    fields = ("status",)
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    template_tag = RenderableTag("action_tags", "action_status_button")
    raise_exception = True

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.visible().connected(user=self.request.user)

    def get_template_tag_args(self, context):
        args = super().get_template_tag_args(context)
        args.update(
            action=context["action"],
        )
        return args

    def form_valid(self, form):
        self.object = form.save()

        # log if the action was changed
        if form.changed_data:
            changed_message = get_verbose_change_message(form=form)
            self.log_change(self.object, changed_message)

        return self.get_response()


class ActionDeleteView(
    ActionsEnabledMixin,
    LogMixin,
    LoginRequiredMixin,
    DeletionMixin,
    SingleObjectMixin,
    View,
):
    model = Action
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    success_url = reverse_lazy("profile:action_list")
    raise_exception = True

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.visible().connected(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # soft-delete
        self.object.is_deleted = True
        self.object.save()

        self.on_delete_action(self.object)

        return HttpResponseRedirect(self.get_success_url())

    def on_delete_action(self, action):
        self.log_deletion(
            action,
            _("action soft-deleted by user {user}").format(user=self.request.user),
        )
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _("Actie '{action}' is verwijdered.").format(action=action),
        )


class ActionCreateView(
    ActionsEnabledMixin,
    LogMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    CreateView,
):
    template_name = "pages/profile/actions/edit.html"
    model = Action
    form_class = ActionForm
    success_url = reverse_lazy("profile:action_list")

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Mijn acties"), reverse("profile:action_list")),
            (
                _("Maak actie aan"),
                reverse("profile:action_create"),
            ),
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(self.request.user)

        self.log_addition(self.object, _("action was created"))
        return HttpResponseRedirect(self.get_success_url())


class ActionListExportView(
    ActionsEnabledMixin, LogMixin, LoginRequiredMixin, ExportMixin, ListView
):
    template_name = "export/profile/action_list_export.html"
    model = Action

    def get_filename(self):
        return "actions.pdf"

    def get_queryset(self):
        base_qs = super().get_queryset()
        return (
            base_qs.visible()
            .filter(Q(is_for=self.request.user) | Q(created_by=self.request.user))
            .select_related("created_by")
        )


class ActionExportView(
    ActionsEnabledMixin, LogMixin, LoginRequiredMixin, ExportMixin, DetailView
):
    template_name = "export/profile/action_export.html"
    model = Action
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.visible().filter(
            Q(is_for=self.request.user) | Q(created_by=self.request.user)
        )


class ActionPrivateMediaView(
    ActionsEnabledMixin, LogMixin, LoginRequiredMixin, PrivateMediaView
):
    model = Action
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    file_field = "file"

    def get_queryset(self):
        return super().get_queryset().visible()

    def has_permission(self):
        action = self.get_object()
        if self.request.user.is_superuser or self.request.user in [
            action.created_by,
            action.is_for,
        ]:
            self.log_user_action(action, _("file was downloaded"))
            return True

        return False


class ActionHistoryView(
    ActionsEnabledMixin,
    LoginRequiredMixin,
    CommonPageMixin,
    BaseBreadcrumbMixin,
    DetailView,
):
    template_name = "pages/history.html"
    model = Action
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    @cached_property
    def crumbs(self):
        return [
            (_("Mijn profiel"), reverse("profile:detail")),
            (_("Mijn acties"), reverse("profile:action_list")),
            (
                _("History of {}").format(self.object.name),
                reverse("profile:action_history", kwargs=self.kwargs),
            ),
        ]

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.visible().connected(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["logs"] = self.object.logs.order_by()
        return context
