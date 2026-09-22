from functools import partial

from django.db import migrations

from open_inwoner.utils.migration_operations import sanitize_prosemirror_link_hrefs

sanitize_content = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="questionnaire",
    model_name="QuestionnaireStep",
    field_name="content",
)


class Migration(migrations.Migration):
    dependencies = [
        ("questionnaire", "0026_alter_questionnairestep_content"),
    ]

    operations = [
        migrations.RunPython(
            code=sanitize_content,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
