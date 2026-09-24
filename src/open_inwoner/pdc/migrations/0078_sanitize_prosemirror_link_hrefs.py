from functools import partial

from django.db import migrations

from open_inwoner.utils.migration_operations import sanitize_prosemirror_link_hrefs

sanitize_category_description = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="pdc",
    model_name="Category",
    field_name="description",
)
sanitize_product_content = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="pdc",
    model_name="Product",
    field_name="content",
)
sanitize_question_answer = partial(
    sanitize_prosemirror_link_hrefs,
    app_label="pdc",
    model_name="Question",
    field_name="answer",
)


class Migration(migrations.Migration):
    dependencies = [
        ("pdc", "0077_alter_question_answer"),
    ]

    operations = [
        migrations.RunPython(
            code=sanitize_category_description,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=sanitize_product_content,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=sanitize_question_answer,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
