from django.db import models
from django.utils.translation import ugettext_lazy as _


class FacetChoices(models.TextChoices):
    categories = "categories", _("Filter op onderwerp")
    tags = "tags", _("Filter op tags")
    organizations = "organizations", _("Filter op organisaties")
