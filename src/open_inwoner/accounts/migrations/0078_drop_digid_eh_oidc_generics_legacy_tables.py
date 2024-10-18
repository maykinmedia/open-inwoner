from django.db import migrations

# The tables for our vendored copy of the digid_eherkenning library
# need to be removed manually before the migrations of the new library
# can be run in order to avoid conflicts due to duplicate tables (the
# db tables from the library use the same app label as our legacy package)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0077_no_roepnaam"),
    ]
    run_before = [
        (
            "digid_eherkenning_oidc_generics",
            "0001_initial_squashed_0007_auto_20221213_1347",
        )
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS digid_eherkenning_oidc_generics_openidconnectdigidconfig;",
        ),
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS digid_eherkenning_oidc_generics_openidconnecteherkenningconfig;",
        ),
    ]
