# Generated by Django 3.2.15 on 2023-03-06 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plans", "0014_auto_20230306_1017"),
    ]

    operations = [
        migrations.AddField(
            model_name="plancontact",
            name="notify_new",
            field=models.BooleanField(default=False, verbose_name="Notify contact"),
        ),
    ]