from functools import partial

from django.db import migrations

from open_inwoner.utils.migration_operations import sanitize_prosemirror_link_hrefs

sanitize_warning_banner_text = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="configurations",
    model_name="SiteConfiguration",
    field_name="warning_banner_text",
)
sanitize_login_text = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="configurations",
    model_name="SiteConfiguration",
    field_name="login_text",
)
sanitize_search_zero_results_text = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="configurations",
    model_name="SiteConfiguration",
    field_name="search_zero_results_text",
)


class Migration(migrations.Migration):
    dependencies = [
        ("configurations", "0101_alter_siteconfiguration_default_colors"),
    ]

    operations = [
        migrations.RunPython(
            code=sanitize_warning_banner_text,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=sanitize_login_text,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=sanitize_search_zero_results_text,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
