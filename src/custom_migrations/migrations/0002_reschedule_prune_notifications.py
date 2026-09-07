from django.db import migrations

TASK_NAME = "Opschonen notificatieberichten"


def _get_crontab(apps, *, minute, hour):
    CrontabSchedule = apps.get_model("django_celery_beat", "CrontabSchedule")
    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=minute,
        hour=hour,
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
        timezone="UTC",
    )
    return schedule


def reschedule_hourly(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    schedule = _get_crontab(apps, minute="0", hour="*")
    PeriodicTask.objects.filter(name=TASK_NAME).update(crontab=schedule)


def reschedule_daily(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    schedule = _get_crontab(apps, minute="0", hour="3")
    PeriodicTask.objects.filter(name=TASK_NAME).update(crontab=schedule)


class Migration(migrations.Migration):
    dependencies = [
        ("custom_migrations", "0001_delete_old_celery_tasks"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(
            code=reschedule_hourly,
            reverse_code=reschedule_daily,
        )
    ]
