from functools import partial

from django.db import migrations

from open_inwoner.utils.migration_operations import sanitize_prosemirror_link_hrefs

sanitize_document_upload_description = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="openzaak",
    model_name="ZaakTypeStatusTypeConfig",
    field_name="document_upload_description",
)
sanitize_description = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="openzaak",
    model_name="ZaakTypeStatusTypeConfig",
    field_name="description",
)


class Migration(migrations.Migration):
    dependencies = [
        ("openzaak", "0086_alter_openzaakconfig_document_visible_statuses"),
    ]

    operations = [
        migrations.RunPython(
            code=sanitize_document_upload_description,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=sanitize_description,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
