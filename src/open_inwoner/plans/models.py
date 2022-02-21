from uuid import uuid4

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from .managers import PlanQuerySet


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
            return file.file

    def get_other_files(self):
        return self.documents.order_by("-created_on")[1:]

    def get_all_files(self):
        return self.documents.order_by("-created_on")
