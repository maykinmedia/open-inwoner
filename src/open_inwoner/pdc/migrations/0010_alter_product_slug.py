from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pdc", "0009_auto_20211027_1732"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(
                help_text="Slug of the product",
                max_length=100,
                unique=True,
                verbose_name="slug",
            ),
        ),
    ]
