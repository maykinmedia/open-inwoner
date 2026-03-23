from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mijn_afval_cms", "0002_create_default_config"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="mijnafvalapphookconfig",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="mijnafvalapphookconfig",
            name="type",
        ),
        migrations.RemoveField(
            model_name="mijnafvalapphookconfig",
            name="app_data",
        ),
    ]
