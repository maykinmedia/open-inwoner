from django.db import migrations


def migrate_invite_email(apps, _):
    Invite = apps.get_model("accounts", "Invite")

    for invite in Invite.objects.select_related("invitee").all():
        invite.invitee_email = invite.invitee.email
        invite.save()


class Migration(migrations.Migration):

    dependencies = [("accounts", "0040_auto_20220518_1456")]

    operations = [migrations.RunPython(migrate_invite_email, migrations.RunPython.noop)]
