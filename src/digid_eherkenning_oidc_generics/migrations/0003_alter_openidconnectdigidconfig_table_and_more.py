# Generated by Django 4.2.11 on 2024-07-08 19:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "digid_eherkenning_oidc_generics_legacy",
            "0002_openidconnectdigidconfig_oidc_token_use_basic_auth_and_more",
        ),
    ]

    run_before = [
        # table needs to be renamed before we start running the migrations of the
        # replacement library
        (
            "digid_eherkenning_oidc_generics",
            "0001_initial_squashed_0007_auto_20221213_1347",
        ),
    ]

    operations = [
        migrations.AlterModelTable(
            name="openidconnectdigidconfig",
            table="digid_eherkenning_oidc_generics_legacy_openidconnectdigidconfig",
        ),
        migrations.AlterModelTable(
            name="openidconnecteherkenningconfig",
            table="digid_eherkenning_oidc_generics_legacy_openidconnecteherkenningconfig",
        ),
    ]
