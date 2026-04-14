from django.db import migrations


def _remove_djangocms_file_content_types(apps, schema_editor):
    """
    Remove stale content type records for the removed djangocms_file app.

    Dropping the tables (see RunSQL operations below) is not enough: Django
    does not automatically remove content types for apps that are removed from
    INSTALLED_APPS.  Stale content type rows cause ``ContentType.model_class()``
    to return ``None`` for those rows.  Any CMS toolbar/versioning code that then
    calls ``ContentType.objects.get_for_model(model_class())`` with that ``None``
    result will crash with::

        AttributeError: 'NoneType' object has no attribute '_meta'
    """
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.filter(app_label="djangocms_file").delete()


def _remove_orphaned_file_cms_plugins(apps, schema_editor):
    """
    Remove orphaned CMS plugin base records whose plugin_type belongs to the
    removed djangocms_file app.

    When djangocms_file is removed, the concrete plugin rows
    (in djangocms_file_file / djangocms_file_folder) are deleted via the
    RunSQL operations below.  However the base cms_cmsplugin rows remain.
    These orphaned base rows cause errors when the toolbar tries to downcast
    them to their concrete plugin type which is no longer registered in
    the plugin pool and whose table no longer exists.
    """
    CMSPlugin = apps.get_model("cms", "CMSPlugin")
    # djangocms_file registers FilePlugin and FolderPlugin
    CMSPlugin.objects.filter(plugin_type__in=["FilePlugin", "FolderPlugin"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("cms", "0001_initial"),
    ]

    operations = [
        # 1. Remove stale content types BEFORE dropping the tables so that any
        #    FK constraints (e.g. Placeholder.content_type → SET_NULL) can fire
        #    cleanly while the tables still exist.
        migrations.RunPython(
            _remove_djangocms_file_content_types,
            migrations.RunPython.noop,
        ),
        # 2. Remove orphaned base CMSPlugin rows for the file plugin types.
        migrations.RunPython(
            _remove_orphaned_file_cms_plugins,
            migrations.RunPython.noop,
        ),
        # 3. Drop the now-empty concrete tables.
        migrations.RunSQL("DROP TABLE IF EXISTS djangocms_file_file;"),
        migrations.RunSQL("DROP TABLE IF EXISTS djangocms_file_folder;"),
    ]
