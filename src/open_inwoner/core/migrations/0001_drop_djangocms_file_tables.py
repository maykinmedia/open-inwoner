from django.db import migrations


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL("DROP TABLE IF EXISTS djangocms_file_file;"),
        migrations.RunSQL("DROP TABLE IF EXISTS djangocms_file_folder;"),
    ]
