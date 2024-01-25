# Generated by Django 3.2.23 on 2024-01-25 11:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0070_auto_20231205_1657"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("login_type", "digid")),
                fields=("bsn",),
                name="unique_bsn_when_login_digid",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("login_type", "eherkenning"), models.Q(("rsin", ""), _negated=True)
                ),
                fields=("rsin",),
                name="unique_rsin_when_login_eherkenning",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("login_type", "eherkenning"), models.Q(("kvk", ""), _negated=True)
                ),
                fields=("kvk",),
                name="unique_kvk_when_login_eherkenning",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("login_type", "oidc")),
                fields=("oidc_id",),
                name="unique_oidc_id_when_login_oidc",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(("bsn", ""), ("login_type", "digid"), _connector="OR"),
                name="check_bsn_only_set_when_login_digid",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("oidc_id", ""), ("login_type", "oidc"), _connector="OR"
                ),
                name="check_oidc_id_only_set_when_login_oidc",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("kvk", ""), ("rsin", "")),
                    ("login_type", "eherkenning"),
                    _connector="OR",
                ),
                name="check_kvk_or_rsin_only_set_when_login_eherkenning",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("kvk", ""), models.Q(("rsin", ""), _negated=True)),
                    models.Q(models.Q(("kvk", ""), _negated=True), ("rsin", "")),
                    models.Q(("login_type", "eherkenning"), _negated=True),
                    _connector="OR",
                ),
                name="check_kvk_or_rsin_exclusive_when_login_eherkenning",
            ),
        ),
    ]
