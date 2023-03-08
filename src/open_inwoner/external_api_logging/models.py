from django.db import models
from django.utils.translation import gettext_lazy as _


class ExternalAPILog(models.Model):
    hostname = models.CharField(
        verbose_name=_("Hostname"),
        max_length=255,
        default="",
        blank=True,
        help_text=_("The hostname part of the url."),
    )
    path = models.CharField(
        verbose_name=_("Path"),
        max_length=255,
        default="",
        blank=True,
        help_text=_("The path part of the url."),
    )
    params = models.TextField(
        verbose_name=_("Parameters"),
        blank=True,
        help_text=_("The parameters (if they exist)."),
    )
    query_params = models.TextField(
        verbose_name=_("Query parameters"),
        blank=True,
        help_text=_("The query parameters part of the url (if they exist)."),
    )
    status_code = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("The status code of the response.")
    )
    method = models.CharField(
        max_length=10, default="", help_text=_("The type of request method.")
    )
    response_ms = models.PositiveIntegerField(
        verbose_name=_("Response in ms"),
        default=0,
        blank=True,
        help_text=_("This is the response time in ms."),
    )
    timestamp = models.DateTimeField(
        verbose_name=_("Timestamp"),
        auto_now_add=True,
        help_text=_("This is the date when the API call was made."),
    )
    user = models.ForeignKey(
        "accounts.User",
        verbose_name=_("User"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The user who made the request."),
    )

    class Meta:
        verbose_name = _("External API Log")
        verbose_name_plural = _("External API Logs")

    def __str__(self):
        return ("{hostname} at {date}").format(
            hostname=self.hostname, date=self.timestamp
        )
