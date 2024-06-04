from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_consumers", "0019_alter_service_uuid"),
        ("openzaak", "0047_delete_statustranslation"),
    ]

    operations = [
        migrations.CreateModel(
            name="ZGWApiGroupConfig",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="A recognisable name for this set of ZGW APIs.",
                        max_length=255,
                        verbose_name="name",
                    ),
                ),
                (
                    "drc_service",
                    models.ForeignKey(
                        limit_choices_to={"api_type": "drc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="zgwset_drc_config",
                        to="zgw_consumers.service",
                        verbose_name="Documenten API",
                    ),
                ),
                (
                    "form_service",
                    models.OneToOneField(
                        limit_choices_to={"api_type": "orc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="zgwset_orc_form_config",
                        to="zgw_consumers.service",
                        verbose_name="Form API",
                    ),
                ),
                (
                    "open_zaak_config",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="api_groups",
                        to="openzaak.openzaakconfig",
                    ),
                ),
                (
                    "zrc_service",
                    models.ForeignKey(
                        limit_choices_to={"api_type": "zrc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="zgwset_zrc_config",
                        to="zgw_consumers.service",
                        verbose_name="Zaken API",
                    ),
                ),
                (
                    "ztc_service",
                    models.ForeignKey(
                        limit_choices_to={"api_type": "ztc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="zgwset_ztc_config",
                        to="zgw_consumers.service",
                        verbose_name="Catalogi API",
                    ),
                ),
            ],
            options={
                "verbose_name": "ZGW API set",
                "verbose_name_plural": "ZGW API sets",
            },
        ),
    ]
