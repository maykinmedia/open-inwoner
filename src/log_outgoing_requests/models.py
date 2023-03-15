from urllib.parse import urlparse

from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _


class OutgoingRequestsLog(models.Model):
    url = models.URLField(
        verbose_name=_("URL"),
        blank=True,
        default="",
        help_text=_("The url of the outgoing request."),
    )
    hostname = models.CharField(
        verbose_name=_("Hostname"),
        max_length=255,
        default="",
        blank=True,
        help_text=_("The hostname part of the url."),
    )
    params = models.TextField(
        verbose_name=_("Parameters"),
        blank=True,
        help_text=_("The parameters (if they exist)."),
    )
    status_code = models.PositiveIntegerField(
        verbose_name=_("Status code"),
        null=True,
        blank=True,
        help_text=_("The status code of the response."),
    )
    method = models.CharField(
        verbose_name=_("Method"),
        max_length=10,
        default="",
        blank=True,
        help_text=_("The type of request method."),
    )
    req_content_type = models.CharField(
        verbose_name=_("Request content type"),
        max_length=50,
        default="",
        blank=True,
        help_text=_("The content type of the request."),
    )
    res_content_type = models.CharField(
        verbose_name=_("Response content type"),
        max_length=50,
        default="",
        blank=True,
        help_text=_("The content type of the response."),
    )
    response_ms = models.PositiveIntegerField(
        verbose_name=_("Response in ms"),
        default=0,
        blank=True,
        help_text=_("This is the response time in ms."),
    )
    timestamp = models.DateTimeField(
        verbose_name=_("Timestamp"),
        help_text=_("This is the date and time the API call was made."),
    )
    trace = models.TextField(
        verbose_name=_("Trace"),
        blank=True,
        null=True,
        help_text=_("Text providing information in case of request failure."),
    )

    class Meta:
        verbose_name = _("Outgoing Requests Log")
        verbose_name_plural = _("Outgoing Requests Logs")

    def __str__(self):
        return ("{hostname} at {date}").format(
            hostname=self.hostname, date=self.timestamp
        )

    @cached_property
    def query_params(self):
        parsed_url = urlparse(self.url)
        return parsed_url.query
