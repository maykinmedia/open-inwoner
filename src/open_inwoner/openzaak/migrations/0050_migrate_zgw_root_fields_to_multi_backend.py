import logging
from django.db import migrations


logger = logging.getLogger(__name__)


def migrate_zgw_service_config_to_default_group_config(apps, schema_editor):
    ZGWApiGroupConfig = apps.get_model("openzaak", "ZGWApiGroupConfig")
    OpenZaakConfig = apps.get_model("openzaak", "OpenZaakConfig")

    for config in OpenZaakConfig.objects.all():
        ZGWApiGroupConfig.objects.create(
            name="Migrated default config",
            zrc_service=config.zaak_service,
            drc_service=config.document_service,
            ztc_service=config.catalogi_service,
            form_service=config.form_service,
            open_zaak_config=config,
        )


def reverse_migrate_zgw_service_config_to_default_group_config(apps, schema_editor):
    OpenZaakConfig = apps.get_model("openzaak", "OpenZaakConfig")

    for config in OpenZaakConfig.objects.all():
        if config.api_groups.count() == 0:
            continue

        if config.api_groups.count() > 1:
            logger.warning("Multiple API groups to choose from, picking first")

        group_config = config.api_groups.first()
        config.zaak_service = group_config.zrc_service
        config.document_service = group_config.drc_service
        config.catalogi_service = group_config.ztc_service
        config.form_service = group_config.form_service
        config.save()


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0049_add_multiple_zgw_backends_config"),
    ]

    operations = [
        migrations.RunPython(
            migrate_zgw_service_config_to_default_group_config,
            reverse_code=reverse_migrate_zgw_service_config_to_default_group_config,
            atomic=True,
        ),
    ]
