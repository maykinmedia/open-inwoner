from django.db import migrations


def normalize_allowed_file_extensions(apps, schema_editor):
    OpenZaakConfig = apps.get_model("openzaak", "OpenZaakConfig")

    for config in OpenZaakConfig.objects.all():
        extensions = []
        for extension in config.allowed_file_extensions:
            extension = extension.strip().lstrip(".").lower()
            if extension and extension not in extensions:
                extensions.append(extension)

        if extensions != config.allowed_file_extensions:
            config.allowed_file_extensions = extensions
            config.save(update_fields=["allowed_file_extensions"])


class Migration(migrations.Migration):
    dependencies = [
        ("openzaak", "0087_sanitize_prosemirror_link_hrefs"),
    ]

    operations = [
        migrations.RunPython(
            code=normalize_allowed_file_extensions,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
