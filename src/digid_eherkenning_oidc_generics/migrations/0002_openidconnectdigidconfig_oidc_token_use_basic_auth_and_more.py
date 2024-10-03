# Generated by Django 4.2.11 on 2024-07-07 13:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("digid_eherkenning_oidc_generics_legacy", "0001_legacy"),
    ]

    # models have the wrong db_table associated
    query1 = """
        ALTER TABLE "digid_eherkenning_oidc_generics_legacy_openidconnectdigidconfig" ADD COLUMN "oidc_token_use_basic_auth" boolean DEFAULT false NOT NULL;
        ALTER TABLE "digid_eherkenning_oidc_generics_legacy_openidconnectdigidconfig" ALTER COLUMN "oidc_token_use_basic_auth" DROP DEFAULT;
    """

    query2 = """
        ALTER TABLE "digid_eherkenning_oidc_generics_legacy_openidconnecteherkenningconfig" ADD COLUMN "oidc_token_use_basic_auth" boolean DEFAULT false NOT NULL;
        ALTER TABLE "digid_eherkenning_oidc_generics_legacy_openidconnecteherkenningconfig" ALTER COLUMN "oidc_token_use_basic_auth" DROP DEFAULT;
    """

    operations = [migrations.RunSQL(query1), migrations.RunSQL(query2)]
