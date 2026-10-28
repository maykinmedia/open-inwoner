from django.db import migrations

CUSTOM_CSP_IDENTIFIER = "migrated-from-custom-csp"


def migrate_to_maykin_common_csp(apps, schema_editor):
    OldCSPSetting = apps.get_model("custom_csp", "CSPSetting")
    CSPSetting = apps.get_model("maykin_common_csp", "CSPSetting")

    CSPSetting.objects.bulk_create(
        CSPSetting(directive=directive, value=value, identifier=CUSTOM_CSP_IDENTIFIER)
        for directive, value in OldCSPSetting.objects.values_list("directive", "value")
    )


def migrate_to_custom_csp(apps, schema_editor):
    OldCSPSetting = apps.get_model("custom_csp", "CSPSetting")
    CSPSetting = apps.get_model("maykin_common_csp", "CSPSetting")

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
