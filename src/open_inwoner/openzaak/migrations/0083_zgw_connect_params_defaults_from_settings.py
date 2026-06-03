import os

from django.db import migrations


def _set_defaults_from_settings(apps, schema_editor):
    OpenZaakConfig = apps.get_model("openzaak", "OpenZaakConfig")
    ZGWApiGroupConfig = apps.get_model("openzaak", "ZGWApiGroupConfig")

    # Read directly from the environment so this migration remains self-contained
    # after the corresponding Django settings are removed.
    num_workers = int(os.environ.get("ZGW_CASE_LIST_NUM_WORKERS", "0")) or None
    fetch_timeout = int(os.environ.get("ZGW_CASE_LIST_FETCH_TIMEOUT", "25"))
    zaken_timeout = int(os.environ.get("CACHE_ZGW_ZAKEN_TIMEOUT", str(60 * 5)))
    catalogi_timeout = int(
        os.environ.get("CACHE_ZGW_CATALOGI_TIMEOUT", str(60 * 60 * 24))
    )

    # Solo model always has pk=1 when it exists; skip if the table is still empty.
    OpenZaakConfig.objects.filter(pk=1).update(
        case_list_num_workers=num_workers,
        case_list_fetch_timeout=fetch_timeout,
    )

    ZGWApiGroupConfig.objects.all().update(
        cache_zaken_timeout=zaken_timeout,
        cache_catalogi_timeout=catalogi_timeout,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("openzaak", "0082_zgw_connect_params_to_models"),
    ]

    operations = [
        migrations.RunPython(
            _set_defaults_from_settings,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
