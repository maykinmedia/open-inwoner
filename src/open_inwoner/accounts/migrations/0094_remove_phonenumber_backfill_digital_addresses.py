from django.db import migrations


def backfill_phone_digital_addresses(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    DigitalAddress = apps.get_model("accounts", "DigitalAddress")

    # Establish the initial DA state that mirrors the current field values:
    # standard DA for phonenumber, non-standard DA for phonenumber_alternative.
    # phonenumber_alternative is about to be dropped; phonenumber stays as a field.
    for user in User.objects.filter(phonenumber__gt=""):
        DigitalAddress.objects.create(
            user=user,
            type="phone",
            value=user.phonenumber,
            login_type=user.login_type,
            is_standard_for_type=True,
        )
        if (
            user.phonenumber_alternative
            and user.phonenumber_alternative != user.phonenumber
        ):
            DigitalAddress.objects.create(
                user=user,
                type="phone",
                value=user.phonenumber_alternative,
                login_type=user.login_type,
                is_standard_for_type=False,
            )


class Migration(migrations.Migration):
    dependencies = [
        (
            "accounts",
            "0093_add_digitaladdress_and_preferred_address",
        ),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="user",
            name="phonenumber_alt_requires_phonenumber_primary",
        ),
        migrations.RemoveConstraint(
            model_name="user",
            name="check_alternative_phonenumber_differs_from_primary_phonenumber",
        ),
        migrations.RunPython(
            backfill_phone_digital_addresses,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="user",
            name="phonenumber_alternative",
        ),
    ]
