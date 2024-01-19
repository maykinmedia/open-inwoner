# Generated by Django 3.2.23 on 2024-01-19 08:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plugins", "0002_userfeed"),
    ]

    operations = [
        migrations.AddField(
            model_name="userfeed",
            name="title",
            field=models.CharField(
                default="Openstaande acties",
                help_text="The title of the plugin block",
                max_length=250,
                verbose_name="Title",
            ),
        ),
    ]
