from django.db import migrations

from zgw_consumers.constants import AuthTypes


def migrate_service_to_api_key_auth(apps, schema_editor):
    """
    OpenKlant2Service used to build its client with `token=service.secret`,
    regardless of the linked Service's `auth_type`. Existing Services were
    therefore configured with the actual Open Klant token in `secret`, even
    though the client now (see the fix in commit 28c72c76) derives its
    Authorization header from `header_key`/`header_value` when
    `auth_type=api_key`.

    Bring any pre-existing linked Service into that expected shape, so the
    fixed client keeps sending the same "Token <secret>" header it used to.
    """
    OpenKlant2Config = apps.get_model("openklant", "OpenKlant2Config")

    config = OpenKlant2Config.objects.first()
    if not config or not config.service_id:
        return

    service = config.service

    already_migrated = (
        service.auth_type == AuthTypes.api_key
        and service.header_key
        and service.header_value
    )
    if already_migrated or not service.secret:
        return

    service.auth_type = AuthTypes.api_key
    service.header_key = "Authorization"
    service.header_value = f"Token {service.secret}"
    service.save(update_fields=["auth_type", "header_key", "header_value"])


class Migration(migrations.Migration):
    dependencies = [
        ("zgw_consumers", "0029_alter_nlxconfig_certificate_and_more"),
        ("openklant", "0040_klantcontactmomentanswer_last_seen_answer_uuid_and_more"),
    ]

    operations = [
        migrations.RunPython(
            migrate_service_to_api_key_auth, migrations.RunPython.noop
        ),
    ]
