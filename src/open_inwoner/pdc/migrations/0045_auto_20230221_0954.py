# Generated by Django 3.2.15 on 2023-02-21 08:54

from django.db import migrations, models
import open_inwoner.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0044_question_category_or_product_null"),
    ]

    operations = [
        migrations.AddField(
            model_name="productlocation",
            name="email",
            field=models.EmailField(
                blank=True,
                help_text="The email address of the current location",
                max_length=254,
                verbose_name="Email address",
            ),
        ),
        migrations.AddField(
            model_name="productlocation",
            name="phonenumber",
            field=models.CharField(
                blank=True,
                default="",
                help_text="The phonenumber of the current location",
                max_length=15,
                validators=[open_inwoner.utils.validators.validate_phone_number],
                verbose_name="Phonenumber",
            ),
        ),
        migrations.AddField(
            model_name="productlocation",
            name="uuid",
            field=models.UUIDField(null=True, verbose_name="UUID"),
        ),
    ]
