from django.db import models
from django.utils.translation import gettext_lazy as _


class ProcessingStatus(models.TextChoices):
    """Status values for notification record processing."""

    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    SUCCESS = "success", _("Success")
    FAILED = "failed", _("Failed")
    SKIPPED = "skipped", _("Skipped")

    @classmethod
    def final_statuses(cls):
        """Return statuses that represent final/terminal states."""
        return (cls.SUCCESS, cls.FAILED, cls.SKIPPED)

    @classmethod
    def retryable_statuses(cls):
        """Return statuses from which a record can be reset for retry."""
        return (cls.FAILED, cls.SUCCESS, cls.SKIPPED)
