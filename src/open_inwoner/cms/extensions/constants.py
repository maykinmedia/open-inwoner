from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class IndicatorChoices(DjangoChoices):
    plan_new_contacts = ChoiceItem("plan_new_contacts", _("Plans > new contacts"))
    inbox_new_messages = ChoiceItem("inbox_new_messages", _("Inbox > new messages"))


class Icons(DjangoChoices):
    apps = ChoiceItem("apps", _("Home"))
    description = ChoiceItem("description", _("Products"))
    inbox = ChoiceItem("inbox", _("Inbox"))
    inventory_2 = ChoiceItem("inventory_2", _("Cases"))
    people = ChoiceItem("people", _("Collaborate"))
    help_outline = ChoiceItem("help_outline", _("Help"))
