from uuid import uuid4

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from filer.fields.file import FilerFileField
from ordered_model.models import OrderedModel


class Plan(models.Model):
    uuid = models.UUIDField(default=uuid4, blank=True, unique=True)
    title = models.CharField(max_length=250, help_text=_("The title of the plan"))
    goal = models.TextField(
        help_text=_(
            "The goal for the plan. So that you and the contact knows what the goal is."
        )
    )
    end_date = models.DateField(help_text=_("When the plan should be archived."))
    contacts = models.ManyToManyField(
        "accounts.Contact",
        related_name="plans",
        help_text=_("The contact that will help you with this plan."),
    )
    created_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
