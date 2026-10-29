from django.db import migrations

PDOK_ACHTERGRONDKAART = (
    "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/"
)

# sources which used to be part of the policy in the settings
SETTINGS_IDENTIFIER = "migrated-from-settings"
# the map tiles are images, so PDOK is only needed in img-src
SETTINGS_OVERRIDES = [
    ("img-src", PDOK_ACHTERGRONDKAART),
]

CUSTOM_CSP_IDENTIFIER = "migrated-from-custom-csp"


def migrate_to_maykin_common_csp(apps, schema_editor):
    OldCSPSetting = apps.get_model("custom_csp", "CSPSetting")
    CSPSetting = apps.get_model("maykin_common_csp", "CSPSetting")

    CSPSetting.objects.bulk_create(
        [
            *(
                CSPSetting(
                    directive=directive,
                    value=value,
                    identifier=CUSTOM_CSP_IDENTIFIER,
                )
                for directive, value in OldCSPSetting.objects.values_list(
                    "directive", "value"
                )
            ),
            *(
                CSPSetting(
                    directive=directive,
                    value=value,
                    identifier=SETTINGS_IDENTIFIER,
                )
                for directive, value in SETTINGS_OVERRIDES
            ),
        ]
    )


def migrate_to_custom_csp(apps, schema_editor):
    OldCSPSetting = apps.get_model("custom_csp", "CSPSetting")
    CSPSetting = apps.get_model("maykin_common_csp", "CSPSetting")

    # the settings provide these sources again after reverting
    CSPSetting.objects.filter(identifier=SETTINGS_IDENTIFIER).delete()

    OldCSPSetting.objects.bulk_create(
        OldCSPSetting(directive=directive, value=value)
        for directive, value in CSPSetting.objects.values_list("directive", "value")
    )
    CSPSetting.objects.filter(identifier=CUSTOM_CSP_IDENTIFIER).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("custom_csp", "0001_initial"),
        ("maykin_common_csp", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            code=migrate_to_maykin_common_csp,
            reverse_code=migrate_to_custom_csp,
        ),
    ]
