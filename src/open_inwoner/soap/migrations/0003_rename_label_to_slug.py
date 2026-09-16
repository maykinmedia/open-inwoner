from django.db import migrations, models
from django.utils.text import slugify


def slugify_existing_labels(apps, schema_editor):
    SoapService = apps.get_model("soap", "SoapService")

    seen = set()
    for service in SoapService.objects.all():
        base = slugify(service.slug) or f"soap-service-{service.pk}"
        slug = base
        suffix = 2
        while slug in seen or (
            SoapService.objects.exclude(pk=service.pk).filter(slug=slug).exists()
        ):
            slug = f"{base}-{suffix}"
            suffix += 1
        seen.add(slug)

        if slug != service.slug:
            service.slug = slug
            service.save(update_fields=["slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("soap", "0002_alter_soapservice_url"),
    ]

    operations = [
        migrations.RenameField(
            model_name="soapservice",
            old_name="label",
            new_name="slug",
        ),
        migrations.RunPython(slugify_existing_labels, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="soapservice",
            name="slug",
            field=models.SlugField(
                help_text="Unique, human-friendly identifier for this service",
                max_length=100,
                unique=True,
                verbose_name="slug",
            ),
        ),
    ]
