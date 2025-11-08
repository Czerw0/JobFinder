from django.shortcuts import render
from .models import Job
from django.core.management import call_command
import threading
import time
from django.utils import timezone
from datetime import timedelta

def home(request):
    return render(request, 'jobfinder/home.html')

def job_list(request):

    def refresh_api():
        print("Refreshing jobs...")
        try:
            call_command('scrape_remotejobs')
            print("Scraping command finished.")
        except Exception as e:
            print(f"An error occurred while refreshing the api: {e}")

    def archive_stale_jobs():
        print("Archiving stale jobs...")

        try:
            archive_threshold = timezone.now() - timedelta(days=60)

            stale_jobs = Job.objects.filter(status=Job.STATUS_ACTIVE, date_last_seen__lt=archive_threshold)
            for job in stale_jobs:
                if job.is_potentially_stale:
                    job.status = Job.STATUS_ARCHIVED
                    job.save()
                    print(f"Archived job: {job.title} at {job.company}")
            print("Archiving process finished.")
        except Exception as e:
            print(f"An error occurred while archiving stale jobs: {e}")


    scraper_thread = threading.Thread(target=refresh_api)
    scraper_thread.start()
    archiver_thread = threading.Thread(target=archive_stale_jobs)
    archiver_thread.start()
    archiver_thread.join()  # Wait for the archiver thread to finish
    archived_jobs_count = Job.objects.filter(status=Job.STATUS_ARCHIVED).count()
    print(f"Archived {archived_jobs_count} jobs")
    jobs = Job.objects.filter(status=Job.STATUS_ACTIVE).order_by('-date_last_seen')
    context = {
        'jobs': jobs
    }
    return render(request, 'jobfinder/job_list.html', context)

