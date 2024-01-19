from django.db import models
from django.utils.translation import ugettext_lazy as _


class FeedItemType(models.TextChoices):
    message_simple = "message_simple", _("Simple text message")
    case_status_changed = "case_status_change", _("Case status changed")
    case_document_added = "case_document_added", _("Case document added")
    plan_expiring = "plan_expiring", _("Plan nears deadline")
