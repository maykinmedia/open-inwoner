import json

from django.db import migrations

import structlog
from django_prosemirror.config import ProsemirrorConfig
from django_prosemirror.constants import EMPTY_DOC
from django_prosemirror.schema import MarkType, NodeType
from django_prosemirror.serde import html_to_doc

logger = structlog.stdlib.get_logger(__name__)


def fix_legacy_text_plugin_body(apps, schema_editor):
    """
    Fix Text plugin body fields that contain legacy or invalid data.

    After replacing djangocms_text_ckeditor with the Prosemirror-based TextPlugin,
    the body column may contain JSON strings (not dicts) from the old plugin:

    - Empty string JSON values ("") -> set to EMPTY_DOC (body column is NOT NULL)
    - Non-empty legacy HTML strings -> convert to Prosemirror JSON via html_to_doc;
      fall back to EMPTY_DOC if conversion fails

    Raw SQL is required because the ProsemirrorModelField descriptor raises
    ValidationError when Django tries to instantiate models with string body values,
    making it impossible to load the corrupt rows via the ORM.
    """

    # Mirror the schema from 0008_add_text_plugin
    config = ProsemirrorConfig(
        allowed_node_types=[
            NodeType.PARAGRAPH,
            NodeType.BLOCKQUOTE,
            NodeType.HORIZONTAL_RULE,
            NodeType.HEADING,
            NodeType.HARD_BREAK,
            NodeType.CODE_BLOCK,
            NodeType.BULLET_LIST,
            NodeType.ORDERED_LIST,
            NodeType.LIST_ITEM,
            NodeType.TABLE,
            NodeType.TABLE_ROW,
            NodeType.TABLE_CELL,
            NodeType.TABLE_HEADER,
        ],
        allowed_mark_types=[
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.LINK,
            MarkType.CODE,
            MarkType.UNDERLINE,
            MarkType.STRIKETHROUGH,
        ],
    )

    fixed_empty = 0
    converted = 0
    failed = 0

    with schema_editor.connection.cursor() as cursor:
        # Cast to text so we get the raw JSON string regardless of whether the
        # psycopg2 JSONB adapter is active; we parse it ourselves below.
        cursor.execute("SELECT cmsplugin_ptr_id, body::text FROM plugins_text")
        rows = cursor.fetchall()

    for plugin_id, raw_text in rows:
        if raw_text is None:
            continue  # SQL NULL — skip
        raw_value = json.loads(raw_text)
        if raw_value is None or isinstance(raw_value, dict):
            continue  # JSONB null or valid Prosemirror dict — skip

        if raw_value == "":
            logger.info(
                "Fixing empty string in Text.body",
                plugin_id=plugin_id,
            )
            with schema_editor.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE plugins_text SET body = %s::jsonb WHERE cmsplugin_ptr_id = %s",
                    (json.dumps(EMPTY_DOC), plugin_id),
                )
            fixed_empty += 1
        elif isinstance(raw_value, str):
            try:
                doc = html_to_doc(raw_value, schema=config.schema)
                with schema_editor.connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE plugins_text SET body = %s::jsonb WHERE cmsplugin_ptr_id = %s",
                        (json.dumps(doc), plugin_id),
                    )
                converted += 1
                logger.info(
                    "Converted legacy HTML in Text.body to Prosemirror JSON",
                    plugin_id=plugin_id,
                )
            except Exception:
                logger.warning(
                    "Could not convert legacy Text.body, setting to EMPTY_DOC",
                    plugin_id=plugin_id,
                    raw_value=raw_value[:100],
                    exc_info=True,
                )
                with schema_editor.connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE plugins_text SET body = %s::jsonb WHERE cmsplugin_ptr_id = %s",
                        (json.dumps(EMPTY_DOC), plugin_id),
                    )
                failed += 1

    logger.info(
        "Completed fixing Text plugin body fields",
        fixed_empty=fixed_empty,
        converted=converted,
        failed=failed,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("plugins", "0014_alter_extendedcmslink_name"),
    ]

    operations = [
        migrations.RunPython(
            code=fix_legacy_text_plugin_body,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
