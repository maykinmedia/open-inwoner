from django.db import migrations


def sync_primary_digital_addresses(apps, schema_editor):
    """
    Ensure every user has standard DigitalAddress records mirroring their
    primary email and phonenumber fields. Uses update_or_create so it is safe
    to run on a database that already has partial DA coverage (e.g. from
    migration 0095 or from update_email/update_phonenumber calls).
    """
    User = apps.get_model("accounts", "User")
    DigitalAddress = apps.get_model("accounts", "DigitalAddress")

    for user in User.objects.filter(email__gt=""):
        # Before creating the standard email DA, remove any non-standard DA
        # that already holds this value to avoid violating
        # unique_digital_address_per_user_type_value.
        DigitalAddress.objects.filter(
            user=user,
            type="email",
            is_standard_for_type=False,
            value=user.email,
        ).delete()
        DigitalAddress.objects.update_or_create(
            user=user,
            type="email",
            is_standard_for_type=True,
            defaults={"value": user.email, "login_type": user.login_type},
        )

    for user in User.objects.filter(phonenumber__gt=""):
        DigitalAddress.objects.filter(
            user=user,
            type="phone",
            is_standard_for_type=False,
            value=user.phonenumber,
        ).delete()
        DigitalAddress.objects.update_or_create(
            user=user,
            type="phone",
            is_standard_for_type=True,
            defaults={"value": user.phonenumber, "login_type": user.login_type},
        )


class Migration(migrations.Migration):
    dependencies = [
        (
            "accounts",
            "0095_remove_phonenumber_backfill_digital_addresses",
        ),
    ]

    operations = [
        migrations.RunPython(
            sync_primary_digital_addresses,
            migrations.RunPython.noop,
        ),
    ]
