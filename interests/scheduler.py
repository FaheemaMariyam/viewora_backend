import json

from django_celery_beat.models import CrontabSchedule, PeriodicTask


def setup_periodic_tasks():
    if PeriodicTask.objects.filter(name="Daily Pending Interest Reminder").exists():
        return

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="9",
        timezone="Asia/Kolkata",
    )

    PeriodicTask.objects.create(
        name="Daily Pending Interest Reminder",
        task="interests.tasks.pending_interest_reminder",
        crontab=schedule,
        args=json.dumps([]),
    )
