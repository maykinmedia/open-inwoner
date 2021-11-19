from django.db import migrations
from django.utils.text import slugify


def migrate_slugs(apps, _):
    Tag = apps.get_model("pdc", "Tag")
    Organization = apps.get_model("pdc", "Organization")

    for tag in Tag.objects.all():
        tag.slug = slugify(tag.name)
        tag.save()

    for organization in Organization.objects.all():
        organization.slug = slugify(organization.name)
        organization.save()


class Migration(migrations.Migration):

    dependencies = [("pdc", "0010_auto_20211119_1158")]

    operations = [migrations.RunPython(migrate_slugs, migrations.RunPython.noop)]
