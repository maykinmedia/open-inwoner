from django.db import models
from django.utils.translation import gettext_lazy as _


class BasicFieldDescription(models.TextChoices):
    ArrayField = _("string, comma-delimited ('foo,bar,baz')")
    BooleanField = "True, False"
    CharField = _("string")
    FileField = _(
        "string represeting the (absolute) path to a file, including file extension: {example}".format(
            example="/absolute/path/to/file.xml"
        )
    )
    ImageField = _(
        "string represeting the (absolute) path to an image file, including file extension: {example}".format(
            example="/absolute/path/to/image.png"
        )
    )
    IntegerField = _("string representing an integer")
    JSONField = _("Mapping: {example}".format(example="{'some_key': 'Some value'}"))
    PositiveIntegerField = _("string representing a positive integer")
    TextField = _("text (string)")
    URLField = _("string (URL)")
    UUIDField = _(
        "UUID string {example}".format(
            example="(e.g. f6b45142-0c60-4ec7-b43d-28ceacdc0b34)"
        )
    )
