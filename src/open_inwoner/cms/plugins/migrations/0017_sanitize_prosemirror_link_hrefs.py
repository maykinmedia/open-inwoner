from functools import partial

from django.db import migrations

from open_inwoner.utils.migration_operations import sanitize_prosemirror_link_hrefs

sanitize_text_body = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="plugins",
    model_name="Text",
    field_name="body",
)


class Migration(migrations.Migration):
    dependencies = [
        ("plugins", "0016_merge_20260504_1103"),
    ]

    operations = [
        migrations.RunPython(
            code=sanitize_text_body,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
