from datetime import timedelta # for calculating time deltas
from django.utils import timezone # for timezone-aware datetime
from django.core.management.base import BaseCommand # base class for management commands
from jobfinder.models import Job 
from jobfinder.logging_config import setup_logger # custom logger setup
logger = setup_logger("archiver", "archive.log")


class Command(BaseCommand):
    """
    Moves jobs that haven't been seen in a very long time to an 'archived' state.
    """
    help = "Archives jobs that are considered very old."

    def handle(self, *args, **options):
        # We consider anything older than 90 days to be "old" — build that cutoff time here.
        archive_threshold = timezone.now() - timedelta(days=90)

        self.stdout.write("Searching for old jobs to archive...")
        
        # Find active jobs that were posted before the cutoff = candidates for archiving.
        jobs_to_archive = Job.objects.filter(
            status=Job.STATUS_ACTIVE,
            date_posted__lt=archive_threshold
        )
        
        count = jobs_to_archive.count()

        if count > 0:
            jobs_to_archive.update(status=Job.STATUS_ARCHIVED)
            success_message = f"Successfully archived {count} old jobs."
            logger.info(success_message)
            self.stdout.write(self.style.SUCCESS(success_message))
        else:
            self.stdout.write(self.style.SUCCESS("No old jobs found to archive."))
