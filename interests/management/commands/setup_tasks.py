import json

from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Registers the pending interest reminder task in Celery Beat"

    def handle(self, *args, **options):
        # 1. Create or get the schedule (9:00 AM Asia/Kolkata)
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="9",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
            timezone="Asia/Kolkata",
        )

        # 2. Register the task
        task, created = PeriodicTask.objects.get_or_create(
            crontab=schedule,
            name="Daily Pending Interest Reminder",
            task="interests.tasks.pending_interest_reminder",
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully registered task: {task.name}")
            )
        else:
            self.stdout.write(self.style.WARNING(f"Task '{task.name}' already exists."))
