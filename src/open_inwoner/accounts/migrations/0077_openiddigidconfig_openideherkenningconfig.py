# Generated by Django 4.2.11 on 2024-07-09 16:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "digid_eherkenning_oidc_generics",
            "0009_remove_digidconfig_oidc_exempt_urls_and_more",
        ),
        ("accounts", "0076_copy_legacy_oidc_digid_eh_configs"),
    ]

    operations = [
        migrations.CreateModel(
            name="OpenIDDigiDConfig",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("digid_eherkenning_oidc_generics.digidconfig",),
        ),
        migrations.CreateModel(
            name="OpenIDEHerkenningConfig",
            fields=[],
            options={
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("digid_eherkenning_oidc_generics.eherkenningconfig",),
        ),
    ]
