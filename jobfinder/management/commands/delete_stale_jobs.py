from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.models import Q
from jobfinder.models import Job
from jobfinder.logging_config import setup_logger

logger = setup_logger("deleter", "delete.log")


class Command(BaseCommand):
    help = "Deletes archived jobs older than 30 days."

    def handle(self, *args, **options):
        delete_threshold = timezone.now() - timedelta(days=35)
        self.stdout.write(f"Searching for archived jobs with date < {delete_threshold.isoformat()} ...")

        qs = Job.objects.filter(
            status=Job.STATUS_ARCHIVED
        ).filter(
            Q(date_last_seen__lt=delete_threshold) | Q(date_posted__lt=delete_threshold)
        )

        count = qs.count()

        if count:
            logger.info("Deleting %s archived jobs older than %s", count, delete_threshold.isoformat())
            qs.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} stale jobs."))
        else:
            self.stdout.write(self.style.SUCCESS("No jobs deleted."))
