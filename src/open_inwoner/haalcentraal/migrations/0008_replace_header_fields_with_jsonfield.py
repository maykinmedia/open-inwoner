import logging  # noqa: TID251

import django.db.models.deletion
from django.db import migrations, models

import django_jsonform.models.fields

import open_inwoner.haalcentraal.validators

logger = logging.getLogger(__name__)

FIELD_TO_HEADER = {
    "api_origin_oin": "x-origin-oin",
    "api_afnemer_oin": "x-afnemer-oin",
    "api_doelbinding": "x-doelbinding",
    "api_verwerking": "x-verwerking",
    "x_request_organization": "x-request-organization",
    "x_request_application": "x-request-application",
    "x_request_afnemerscode": "x-request-afnemerscode",
    "x_request_user": "x-request-user",
}

_HEADERS_HELP_TEXT = (
    "Key/value pairs sent as additional HTTP headers on each BRP request. "
    "Refer to your vendor's documentation for more information about these headers. "
    "iConnect example keys: 'x-origin-oin', 'x-afnemer-oin', 'x-doelbinding', 'x-verwerking'. "
    "Centric: 'x-request-organization', 'x-request-application', "
    "'x-request-afnemerscode', 'x-request-user'."
)


def migrate_headers_and_add_x_gebruiker(apps, schema_editor):
    """
    Migrate individual header fields to the new headers list and append
    x-gebruiker: BurgerZelf for BRP 2.x configs (previously hardcoded in client).
    """
    HaalCentraalConfig = apps.get_model("haalcentraal", "HaalCentraalConfig")
    config = HaalCentraalConfig.objects.first()
    if not config:
        return

    headers = []
    for field, header_key in FIELD_TO_HEADER.items():
        value = getattr(config, field, "")
        if value:
            headers.append({"key": header_key, "value": value})

    if config.brp_version in ("2.0", "2.1"):
        existing_keys = {item["key"] for item in headers}
        if "x-gebruiker" not in existing_keys:
            headers.append({"key": "x-gebruiker", "value": "BurgerZelf"})
            logger.info("Added x-gebruiker: BurgerZelf to HaalCentraalConfig headers.")

    config.headers = headers
    config.save()


class Migration(migrations.Migration):
    dependencies = [
        ("haalcentraal", "0007_haalcentraalconfig_brp_version"),
        ("zgw_consumers", "0025_service_jwt_valid_for"),
    ]

    operations = [
        migrations.AddField(
            model_name="haalcentraalconfig",
            name="headers",
            field=django_jsonform.models.fields.JSONField(
                blank=True,
                default=list,
                help_text=_HEADERS_HELP_TEXT,
                validators=[
                    open_inwoner.haalcentraal.validators.validate_no_standard_http_headers
                ],
                verbose_name="Request headers",
            ),
        ),
        # Migrate old fields directly to list format and add x-gebruiker for 2.x
        migrations.RunPython(
            migrate_headers_and_add_x_gebruiker, migrations.RunPython.noop
        ),
        # Remove the old individual header fields
        migrations.RemoveField(model_name="haalcentraalconfig", name="api_origin_oin"),
        migrations.RemoveField(model_name="haalcentraalconfig", name="api_afnemer_oin"),
        migrations.RemoveField(model_name="haalcentraalconfig", name="api_doelbinding"),
        migrations.RemoveField(model_name="haalcentraalconfig", name="api_verwerking"),
        migrations.RemoveField(
            model_name="haalcentraalconfig", name="x_request_organization"
        ),
        migrations.RemoveField(
            model_name="haalcentraalconfig", name="x_request_application"
        ),
        migrations.RemoveField(
            model_name="haalcentraalconfig", name="x_request_afnemerscode"
        ),
        migrations.RemoveField(model_name="haalcentraalconfig", name="x_request_user"),
        migrations.AlterField(
            model_name="haalcentraalconfig",
            name="service",
            field=models.OneToOneField(
                help_text="Configure the request headers for the chosen API service below.",
                limit_choices_to={"api_type": "orc"},
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="zgw_consumers.service",
                verbose_name="Haal Centraal API",
            ),
        ),
        migrations.AlterField(
            model_name="haalcentraalconfig",
            name="brp_version",
            field=models.CharField(
                choices=[("1.3", "BRP 1.3"), ("2.0", "BRP 2.0"), ("2.1", "BRP 2.1")],
                default="2.0",
                help_text=(
                    "Version of the Haal Centraal BRP API to use. "
                    "See https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc "
                    "for the API specification."
                ),
                max_length=3,
                verbose_name="BRP version",
            ),
        ),
    ]
