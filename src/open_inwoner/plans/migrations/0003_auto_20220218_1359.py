# Generated by Django 3.2.12 on 2022-02-18 12:59

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0029_auto_20220218_1359"),
        ("plans", "0002_auto_20220214_1440"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="plan",
            options={"verbose_name": "Plan", "verbose_name_plural": "Plans"},
        ),
        migrations.AlterField(
            model_name="plan",
            name="contacts",
            field=models.ManyToManyField(
                help_text="The contact that will help you with this plan.",
                related_name="plans",
                to="accounts.Contact",
                verbose_name="Contacts",
            ),
        ),
        migrations.AlterField(
            model_name="plan",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
        ),
        migrations.AlterField(
            model_name="plan",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="Created by",
            ),
        ),
        migrations.AlterField(
            model_name="plan",
            name="end_date",
            field=models.DateField(
                help_text="When the plan should be archived.", verbose_name="End date"
            ),
        ),
        migrations.AlterField(
            model_name="plan",
            name="goal",
            field=models.TextField(
                help_text="The goal for the plan. So that you and the contact knows what the goal is.",
                verbose_name="Goal",
            ),
        ),
        migrations.AlterField(
            model_name="plan",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated at"),
        ),
        migrations.AlterField(
            model_name="plan",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, unique=True, verbose_name="UUID"
            ),
        ),
    ]
