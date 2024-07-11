from django.contrib import postgres
from django.db import models

basic_field_descriptions = {
    postgres.fields.ArrayField: "string, comma-delimited ('foo,bar,baz')",
    models.BooleanField: "True, False",
    models.CharField: "string",
    models.EmailField: "string representing an Email address (foo@bar.com)",
    models.FileField: (
        "string representing the (absolute) path to a file, "
        "including file extension: {example}".format(
            example="/absolute/path/to/file.xml"
        )
    ),
    models.ImageField: (
        "string representing the (absolute) path to an image file, "
        "including file extension: {example}".format(
            example="/absolute/path/to/image.png"
        )
    ),
    models.IntegerField: "string representing an integer",
    models.JSONField: "Mapping: {example}".format(example="{'some_key': 'Some value'}"),
    models.PositiveIntegerField: "string representing a positive integer",
    models.TextField: "text (string)",
    models.URLField: "string (URL)",
    models.UUIDField: "UUID string {example}".format(
        example="(e.g. f6b45142-0c60-4ec7-b43d-28ceacdc0b34)"
    ),
}
