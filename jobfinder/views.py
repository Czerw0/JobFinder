from django.shortcuts import render
from .models import Job
from django.core.management import call_command
import threading
from django.utils import timezone
from datetime import timedelta
from jobfinder.logging_config import setup_logger

# Setup loggers
scraper_logger = setup_logger("scraper", "scraper.log")
archiver_logger = setup_logger("archiver", "archive.log")

def home(request):
    return render(request, 'jobfinder/home.html')


def job_list(request):

    def refresh_api():
        scraper_logger.info("Refreshing jobs...")
        try:
            call_command('scrape_remotejobs')
            scraper_logger.info("Scraping command finished.")
        except Exception as e:
            scraper_logger.error(f"An error occurred while refreshing the API: {e}", exc_info=True)

    def archive_stale_jobs():
        archiver_logger.info("Archiving stale jobs...")

        try:
            archive_threshold = timezone.now() - timedelta(days=60)

            stale_jobs = Job.objects.filter(
                status=Job.STATUS_ACTIVE,
                date_last_seen__lt=archive_threshold
            )

            for job in stale_jobs:
                job.status = Job.STATUS_ARCHIVED
                job.save()
                archiver_logger.info(f"Archived job: {job.title} at {job.company}")

            archived_count = stale_jobs.count()
            archiver_logger.info(f"Archiving process finished. Archived {archived_count} jobs.")

        except Exception as e:
            archiver_logger.error(f"Error while archiving stale jobs: {e}", exc_info=True)

    # Run both threads
    scraper_thread = threading.Thread(target=refresh_api)
    scraper_thread.start()

    archiver_thread = threading.Thread(target=archive_stale_jobs)
    archiver_thread.start()
    archiver_thread.join()

    # Query for active jobs
    jobs = Job.objects.filter(status=Job.STATUS_ACTIVE).order_by('-date_last_seen')

    context = {'jobs': jobs}
    return render(request, 'jobfinder/job_list.html', context)
