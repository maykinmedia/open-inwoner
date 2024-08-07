# Generated by Django 4.2.11 on 2024-07-09 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0067_alter_siteconfiguration_warning_banner_text"),
    ]

    operations = [
        migrations.RenameField(
            model_name="siteconfiguration",
            old_name="email_new_message",
            new_name="notifications_messages_enabled",
        ),
        migrations.AlterField(
            model_name="siteconfiguration",
            name="notifications_messages_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Notify users of new messages (if set, individual users can still opt out)",
                verbose_name="User notifications for messages",
            ),
        ),
        migrations.AddField(
            model_name="siteconfiguration",
            name="notifications_actions_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Notify users of expiring actions (if set, individual users can still opt out)",
                verbose_name="User notifications for expiring actions",
            ),
        ),
        migrations.AddField(
            model_name="siteconfiguration",
            name="notifications_cases_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Notify users of upddates to cases or if an action is required (if set, individual users can still opt out)",
                verbose_name="User notifications for cases",
            ),
        ),
        migrations.AddField(
            model_name="siteconfiguration",
            name="notifications_plans_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Notify users of expiring plans (if set, individual users can still opt out)",
                verbose_name="User notifications for expiring plans",
            ),
        ),
    ]