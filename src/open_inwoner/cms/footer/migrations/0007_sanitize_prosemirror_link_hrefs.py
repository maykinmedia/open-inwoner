from functools import partial

from django.db import migrations

from open_inwoner.utils.migration_operations import sanitize_prosemirror_link_hrefs

sanitize_content = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="footer",
    model_name="CMSFlatPageModel",
    field_name="content",
)


class Migration(migrations.Migration):
    dependencies = [
        ("footer", "0006_alter_cmsflatpagemodel_content"),
    ]

    operations = [
        migrations.RunPython(
            code=sanitize_content,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
