from uuid import uuid4

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from filer.fields.file import FilerFileField

from open_inwoner.accounts.choices import TypeChoices

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

    def __str__(self):
        return self.name


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
    goal = models.CharField(
        verbose_name=_("goal"),
        default="",
        blank=True,
        max_length=250,
        help_text=_(
            "The goal that will be applied to the action if this template in chosen."
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
    end_date = models.DateField(
        verbose_name=_("End date"), help_text=_("When the plan should be archived.")
    )
    contacts = models.ManyToManyField(
        "accounts.Contact",
        verbose_name=_("Contacts"),
        related_name="plans",
        blank=True,
        help_text=_("The contact that will help you with this plan."),
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

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("plans:plan_detail", kwargs={"uuid": self.uuid})

    def contactperson_list(self):
        return ", ".join([contact.get_name() for contact in self.contacts.all()])

    def get_latest_file(self):
        file = self.documents.order_by("-created_on").first()
        if file:
            return file

    def get_other_files(self):
        return self.documents.order_by("-created_on")[1:]

    def get_all_files(self):
        return self.documents.order_by("-created_on")
