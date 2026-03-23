from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("profile", "0009_profileconfig_appointments"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="profileconfig",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="profileconfig",
            name="type",
        ),
        migrations.RemoveField(
            model_name="profileconfig",
            name="app_data",
        ),
    ]
