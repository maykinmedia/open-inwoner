from datetime import date
from uuid import uuid4

from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from filer.fields.file import FilerFileField

from open_inwoner.accounts.choices import StatusChoices, TypeChoices

from .managers import PlanQuerySet


class PlanTemplate(models.Model):
    name = models.CharField(
        _("Name"),
        max_length=250,
        help_text=_(
            "The name of the plan template. Will not be copied over to the plan."
        ),
    )
    file = FilerFileField(
        verbose_name=_("File"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_(
            "The initial file of the plan. This could be a template for the final product."
        ),
    )
    goal = models.TextField(
        _("goal"),
        help_text=_(
            "The goal for the plan. So that you and the contact knows what the goal is."
        ),
    )
    description = models.TextField(
        verbose_name=_("description"),
        default="",
        blank=True,
        help_text=_("The description of the plan."),
    )

    def __str__(self):
        return self.name

    def string_preview(self):
        return render_to_string("plans/preview.html", {"plan_template": self})


class ActionTemplate(models.Model):
    plan_template = models.ForeignKey(
        "plans.PlanTemplate",
        verbose_name=_("Plan template"),
        on_delete=models.CASCADE,
        related_name="actiontemplates",
        help_text=_("The plan template the action belongs to."),
    )
    name = models.CharField(
        verbose_name=_("Name"),
        default="",
        max_length=250,
        help_text=_(
            "The name that will be applied to the action if this template in chosen."
        ),
    )
    description = models.TextField(
        verbose_name=_("description"),
        default="",
        blank=True,
        help_text=_(
            "The description that will be applied to the action if this template in chosen."
        ),
    )
    type = models.CharField(
        verbose_name=_("Type"),
        default=TypeChoices.incidental,
        max_length=200,
        choices=TypeChoices.choices,
        help_text=_(
            "The type of action that will be applied to the action if this template in chosen."
        ),
    )
    end_in_days = models.PositiveIntegerField(
        verbose_name=_("Ends in x days"),
        help_text=_("End date is set X days in the future if this template is chosen"),
    )


class PlanContact(models.Model):
    plan = models.ForeignKey(
        "plans.Plan", verbose_name=_("Plan"), on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "accounts.User", verbose_name=_("Contact"), on_delete=models.CASCADE
    )
    notify_new = models.BooleanField(verbose_name=_("Notify contact"), default=True)


class Plan(models.Model):
    uuid = models.UUIDField(verbose_name=_("UUID"), default=uuid4, unique=True)
    title = models.CharField(
        verbose_name=_("Title"), max_length=250, help_text=_("The title of the plan")
    )
    goal = models.TextField(
        verbose_name=_("Goal"),
        help_text=_(
            "The goal for the plan. So that you and the contact knows what the goal is."
        ),
    )
    description = models.TextField(
        verbose_name=_("description"),
        default="",
        blank=True,
        help_text=_("The description of the plan."),
    )
    end_date = models.DateField(
        verbose_name=_("End date"), help_text=_("When the plan should be archived.")
    )
    plan_contacts = models.ManyToManyField(
        "accounts.User",
        verbose_name=_("Contacts"),
        related_name="plans",
        blank=True,
        help_text=_("The contact that will help you with this plan."),
        through=PlanContact,
    )
    created_by = models.ForeignKey(
        "accounts.User", verbose_name=_("Created by"), on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(verbose_name=_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Updated at"), auto_now=True)

    objects = PlanQuerySet.as_manager()

    class Meta:
        verbose_name = _("Plan")
        verbose_name_plural = _("Plans")
        ordering = ("end_date",)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("collaborate:plan_detail", kwargs={"uuid": self.uuid})

    def get_latest_file(self):
        file = self.documents.order_by("-created_on").first()
        if file:
            return file

    def get_other_files(self):
        return self.documents.order_by("-created_on")[1:]

    def get_all_files(self):
        return self.documents.order_by("-created_on")

    def get_other_users(self, user=None):
        """return list of users participating in the plan with exception of the current user"""
        contacts_ids = self.plan_contacts.values_list("pk", flat=True)
        user_ids = {self.created_by.id, *contacts_ids}

        if user and user.id in user_ids:
            user_ids.remove(user.id)

        from open_inwoner.accounts.models import User

        return User.objects.filter(id__in=user_ids)

    def get_other_users_full_names(self, user):
        other_users = self.get_other_users(user)
        return ", ".join([user.get_full_name() for user in other_users])

    def get_status(self):
        if self.end_date > date.today():
            return _("Open")
        else:
            return _("Afgerond")

    def open_actions(self):
        return self.actions.filter(
            Q(status=StatusChoices.open) | Q(status=StatusChoices.approval),
            is_deleted=False,
        )
