from django.db import migrations


def migrate_seen(apps, _):
    """mark all old messages as seen for now"""
    Message = apps.get_model("accounts", "Message")

    Message.objects.update(seen=True)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0024_merge_0021_alter_contact_type_0023_auto_20220202_0951")
    ]

    operations = [migrations.RunPython(migrate_seen, migrations.RunPython.noop)]
