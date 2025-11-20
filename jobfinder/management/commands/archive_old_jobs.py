import logging
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from jobfinder.models import Job

logger = logging.getLogger("archiver")

class Command(BaseCommand):
    """
    Moves jobs that haven't been seen in a very long time to an 'archived' state.
    """
    help = "Archives jobs that are considered very old."

    def handle(self, *args, **options):
        # Define the threshold for archiving. 90 days is a reasonable default.
        archive_threshold = timezone.now() - timedelta(days=90)

        self.stdout.write("Searching for very old jobs to archive...")
        
        # Find active jobs last seen more than 90 days ago.
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