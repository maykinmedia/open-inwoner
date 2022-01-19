# Generated by Django 3.2.7 on 2022-01-10 16:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plans", "0004_alter_goal_explaination"),
    ]

    operations = [
        migrations.AlterField(
            model_name="goal",
            name="explaination",
            field=models.TextField(help_text=""),
        ),
        migrations.AlterField(
            model_name="goal",
            name="plan",
            field=models.ForeignKey(
                help_text="The plan what the goal is for.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="goals",
                to="plans.plan",
            ),
        ),
        migrations.AlterField(
            model_name="planfile",
            name="plan",
            field=models.ForeignKey(
                help_text="To which plan the file belongs to",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="files",
                to="plans.plan",
            ),
        ),
    ]
