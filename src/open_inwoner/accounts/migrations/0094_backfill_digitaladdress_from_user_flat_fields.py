from django.db import migrations


def backfill_digital_addresses(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    DigitalAddress = apps.get_model("accounts", "DigitalAddress")

    email_addresses = []
    other_addresses = []
    for user in User.objects.only(
        "id", "email", "phonenumber", "phonenumber_alternative", "login_type"
    ):
        email_addresses.append(
            DigitalAddress(
                user=user,
                type="email",
                value=user.email,
                login_type=user.login_type,
            )
        )
        if user.phonenumber:
            other_addresses.append(
                DigitalAddress(
                    user=user,
                    type="phone",
                    value=user.phonenumber,
                    login_type=user.login_type,
                )
            )
        if user.phonenumber_alternative:
            other_addresses.append(
                DigitalAddress(
                    user=user,
                    type="phone",
                    value=user.phonenumber_alternative,
                    login_type=user.login_type,
                )
            )

    created_emails = DigitalAddress.objects.bulk_create(email_addresses)
    DigitalAddress.objects.bulk_create(other_addresses)

    users_to_update = []
    for addr in created_emails:
        addr.user.preferred_address = addr
        users_to_update.append(addr.user)
    User.objects.bulk_update(users_to_update, ["preferred_address"])


def reverse_backfill_digital_addresses(apps, schema_editor):
    DigitalAddress = apps.get_model("accounts", "DigitalAddress")
    DigitalAddress.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0093_add_digitaladdress_and_preferred_address"),
    ]

    operations = [
        migrations.RunPython(
            backfill_digital_addresses,
            reverse_code=reverse_backfill_digital_addresses,
        ),
    ]
