from django.conf import settings
from django.db import migrations


def forwards(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")

    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(user_app_label, user_model_name)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # Get all permissions related to the Title model
    title_permissions = Permission.objects.filter(
        content_type__app_label="cms", content_type__model="pagecontent"
    )

    pageversion, _ = ContentType.objects.get_or_create(
        app_label="djangocms_versioning", model="pagecontentversion"
    )
    for perm in title_permissions:
        # Create the same permission for the PageContent model
        version_perm, _ = Permission.objects.get_or_create(
            codename=perm.codename.replace("_title", "_pagecontentversion"),
            name=perm.name.replace(" title", " pagecontentversion"),
            content_type=pageversion,
        )
        # Update existing permissions
        perm.codename = perm.codename.replace("_title", "_pagecontent")
        perm.name = perm.name.replace(" title", " pagecontent")
        perm.save()
        # Assign the new permission to users and groups
        for user in User.objects.filter(user_permissions=perm):
            user.user_permissions.add(version_perm)

        for group in Group.objects.filter(permissions=perm):
            group.permissions.add(version_perm)


class Migration(migrations.Migration):
    dependencies = [
        ("djangocms_4_migration", "0003_page_version_integration_data_migration"),
    ]

    operations = [
        migrations.RunPython(forwards),
    ]
