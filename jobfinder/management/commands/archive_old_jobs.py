from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.models import Q
from jobfinder.models import Job
from jobfinder.logging_config import setup_logger
logger = setup_logger("archiver", "archive.log")


class Command(BaseCommand):
    help = "Archives jobs that are no longer active based on last seen or posted date."

    def handle(self, *args, **options):
        # archive jobs not seen/posted for 30 days
        threshold = timezone.now() - timedelta(days=30)

        self.stdout.write(f"Archiving jobs older than {threshold.isoformat()} ...")

        qs = Job.objects.filter(
            status=Job.STATUS_ACTIVE
        ).filter(
            Q(date_last_seen__lt=threshold) | Q(date_posted__lt=threshold)
        )

        count = qs.count()

        if count:
            qs.update(status=Job.STATUS_ARCHIVED)
            msg = f"Archived {count} stale jobs."
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        else:
            self.stdout.write(self.style.SUCCESS("No stale jobs found."))



