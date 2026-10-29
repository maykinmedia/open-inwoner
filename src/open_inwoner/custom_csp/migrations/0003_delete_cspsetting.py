from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("custom_csp", "0002_migrate_to_maykin_common_csp"),
    ]

    operations = [
        migrations.DeleteModel(
            name="CSPSetting",
        ),
    ]
