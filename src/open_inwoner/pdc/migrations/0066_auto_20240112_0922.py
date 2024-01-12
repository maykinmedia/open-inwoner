# Generated by Django 3.2.23 on 2024-01-12 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0065_product_auto_redirect_to_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="auto_redirect_to_link",
            field=models.BooleanField(
                default=False,
                help_text="Whether the user should be automatically redirect to the category link when the user visits the product page.",
                verbose_name="Automatically redirect to link",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="link",
            field=models.URLField(
                blank=True,
                default="",
                help_text="The link to which the user will be redirected",
                max_length=1000,
                verbose_name="Redirect to link",
            ),
        ),
    ]