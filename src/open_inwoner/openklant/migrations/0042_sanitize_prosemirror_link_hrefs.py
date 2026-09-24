from functools import partial

from django.db import migrations

from open_inwoner.utils.migration_operations import sanitize_prosemirror_link_hrefs

sanitize_description_authenticated_user = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="openklant",
    model_name="ContactFormConfig",
    field_name="description_authenticated_user",
)
sanitize_description_anonymous_user = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="openklant",
    model_name="ContactFormConfig",
    field_name="description_anonymous_user",
)


class Migration(migrations.Migration):
    dependencies = [
        ("openklant", "0041_migrate_openklant2_service_auth"),
    ]

    operations = [
        migrations.RunPython(
            code=sanitize_description_authenticated_user,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=sanitize_description_anonymous_user,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
