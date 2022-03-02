# Generated by Django 3.2.12 on 2022-02-07 11:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0021_merge_20220202_1847"),
    ]

    operations = [
        migrations.CreateModel(
            name="Question",
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
                    "order",
                    models.PositiveIntegerField(
                        db_index=True, editable=False, verbose_name="order"
                    ),
                ),
                ("question", models.CharField(max_length=250, verbose_name="Vraag")),
                ("answer", models.TextField(verbose_name="Antwoord")),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="pdc.category"
                    ),
                ),
            ],
            options={
                "verbose_name": "Vraag",
                "verbose_name_plural": "FAQ vragen",
                "ordering": ("category", "order"),
                "abstract": False,
            },
        ),
    ]
