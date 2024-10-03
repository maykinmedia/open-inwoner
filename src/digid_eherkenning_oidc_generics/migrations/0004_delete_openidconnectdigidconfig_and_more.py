# Generated by Django 4.2.11 on 2024-07-09 16:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "digid_eherkenning_oidc_generics_legacy",
            "0003_alter_openidconnectdigidconfig_table_and_more",
        ),
        (
            "accounts",
            "0077_openiddigidconfig_openideherkenningconfig",
        ),
    ]

    # models have the wrong db_table associated
    query1 = """
        DROP TABLE "digid_eherkenning_oidc_generics_legacy_openidconnectdigidconfig" CASCADE;
    """

    query2 = """
        DROP TABLE "digid_eherkenning_oidc_generics_legacy_openidconnecteherkenningconfig" CASCADE;
    """

    operations = [migrations.RunSQL(query1), migrations.RunSQL(query2)]
