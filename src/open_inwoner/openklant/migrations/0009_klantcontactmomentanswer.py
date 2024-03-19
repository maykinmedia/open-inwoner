# Generated by Django 4.2.10 on 2024-03-15 15:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("openklant", "0008_openklantconfig_use_rsin_for_innnnpid_query_parameter"),
    ]

    operations = [
        migrations.CreateModel(
            name="KlantContactMomentAnswer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "contactmoment_url",
                    models.URLField(max_length=1000, verbose_name="ContactMoment URL"),
                ),
                (
                    "is_seen",
                    models.BooleanField(
                        default=False,
                        help_text="Whether or not the user has seen the answer",
                        verbose_name="Is seen",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="This is the user that asked the question to which this is an answer.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contactmoment_answers",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "KlantContactMoment",
                "verbose_name_plural": "KlantContactMomenten",
                "unique_together": {("user", "contactmoment_url")},
            },
        ),
    ]