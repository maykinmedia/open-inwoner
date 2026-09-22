from functools import partial

from django.db import migrations

from open_inwoner.utils.migration_operations import sanitize_prosemirror_link_hrefs

sanitize_jaaropgave_display_text = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="ssd",
    model_name="SSDConfig",
    field_name="jaaropgave_display_text",
)
sanitize_maandspecificatie_display_text = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="ssd",
    model_name="SSDConfig",
    field_name="maandspecificatie_display_text",
)


class Migration(migrations.Migration):
    dependencies = [
        ("ssd", "0019_alter_ssdconfig_jaaropgave_display_text_and_more"),
    ]

    operations = [
        migrations.RunPython(
            code=sanitize_jaaropgave_display_text,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=sanitize_maandspecificatie_display_text,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
