from django.db import migrations
from open_inwoner.utils.hash import generate_email_from_string
from ..choices import LoginTypeChoices


def change_bsn_email_to_hash(apps, _):
    User = apps.get_model("accounts", "User")

    for user in User.objects.filter(login_type=LoginTypeChoices.digid).all():
        if user.email == f"user-{user.bsn}@bsn.com":
            user.email = generate_email_from_string(user.bsn)
            user.save()


def change_hash_email_to_bsn(apps, _):
    User = apps.get_model("accounts", "User")

    for user in User.objects.filter(login_type=LoginTypeChoices.digid).all():
        if user.email == generate_email_from_string(user.bsn):
            user.email = f"user-{user.bsn}@bsn.com"
            user.save()


class Migration(migrations.Migration):

    dependencies = [("accounts", "0042_alter_invite_invitee_email")]

    operations = [
        migrations.RunPython(change_bsn_email_to_hash, change_hash_email_to_bsn)
    ]
