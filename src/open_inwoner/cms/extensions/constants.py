from django.db import models
from django.utils.translation import gettext_lazy as _


class IndicatorChoices(models.TextChoices):
    plan_new_contacts = "plan_new_contacts", _("Plans > new contacts")
    inbox_new_messages = "inbox_new_messages", _("Inbox > new messages")


class Icons(models.TextChoices):
    person = "person", _("Home")
    description = "description", _("Products")
    inbox = "inbox", _("Inbox")
    inventory_2 = "inventory_2", _("Cases")
    group = "group", _("Collaborate")
    help_outline = "help_outline", _("Help")
    euro_outline = "euro_outline", _("Benefits")
