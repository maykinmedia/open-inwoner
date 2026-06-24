from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "accounts",
            "0096_sync_primary_email_phonenumber_digital_addresses",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="digitaladdress",
            options={
                "ordering": ["-is_standard_for_type", "created_at"],
                "verbose_name": "Digital address",
                "verbose_name_plural": "Digital addresses",
            },
        ),
    ]
