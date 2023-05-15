# Generated by Django 3.2.15 on 2023-04-28 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("extensions", "0002_commonextension_menu_indicator"),
    ]

    operations = [
        migrations.AddField(
            model_name="commonextension",
            name="menu_icon",
            field=models.CharField(
                blank=True,
                choices=[
                    ("apps", "Home"),
                    ("description", "Products"),
                    ("inbox", "Inbox"),
                    ("inventory_2", "Cases"),
                    ("people", "Collaborate"),
                    ("help_outline", "Help"),
                ],
                help_text="Icon in het menu",
                max_length=32,
                verbose_name="Icon",
            ),
        ),
    ]