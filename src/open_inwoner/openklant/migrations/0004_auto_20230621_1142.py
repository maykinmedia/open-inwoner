# Generated by Django 3.2.15 on 2023-06-21 09:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("openklant", "0003_auto_20230526_1013"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="contactformsubject",
            options={
                "ordering": ("order",),
                "verbose_name": "Contact formulier onderwerp",
                "verbose_name_plural": "Contact formulier onderwerpen",
            },
        ),
        migrations.AddField(
            model_name="contactformsubject",
            name="order",
            field=models.PositiveIntegerField(
                db_index=True, editable=False, null=True, verbose_name="order"
            ),
        ),
    ]
