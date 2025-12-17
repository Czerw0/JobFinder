from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import threading

from .models import Job
from .match_jobs import match_jobs_to_cv
from users.models import CV
from jobfinder.logging_config import setup_logger

# Setup loggers
scraper_logger = setup_logger("scraper", "scraper.log")
archiver_logger = setup_logger("archiver", "archive.log")


def home(request):
    return render(request, 'jobfinder/home.html')


def job_list(request):
    """
    Shows all active jobs.
    Refreshes API + archives stale jobs in background threads.
    """

    def refresh_api():
        scraper_logger.info("Refreshing jobs...")
        try:
            call_command('scrape_remotejobs')
            scraper_logger.info("Scraping finished.")
        except Exception as e:
            scraper_logger.error(f"Scraping error: {e}", exc_info=True)

    def archive_stale_jobs():
        archiver_logger.info("Archiving stale jobs...")
        try:
            threshold = timezone.now() - timedelta(days=60)
            stale_jobs = Job.objects.filter(
                status=Job.STATUS_ACTIVE,
                date_last_seen__lt=threshold
            )

            for job in stale_jobs:
                job.status = Job.STATUS_ARCHIVED
                job.save()
                archiver_logger.info(f"Archived: {job.title}")

        except Exception as e:
            archiver_logger.error(f"Archiving error: {e}", exc_info=True)

    threading.Thread(target=refresh_api).start()
    archiver_thread = threading.Thread(target=archive_stale_jobs)
    archiver_thread.start()
    archiver_thread.join()

    jobs = Job.objects.filter(status=Job.STATUS_ACTIVE).order_by('-date_last_seen')
    return render(request, 'jobfinder/job_list.html', {'jobs': jobs})


# MATCHING – JSON API
@require_GET
def match_jobs(request, cv_id):
    """
    API endpoint returning ranked jobs with scores.
    """

    try:
        top_n = int(request.GET.get("top", 5))
    except ValueError:
        return JsonResponse({"error": "top must be integer"}, status=400)

    cv = get_object_or_404(CV, id=cv_id)

    results = match_jobs_to_cv(cv.id, top_n)

    data = [
        {
            "job_id": r["job"].id,
            "title": r["job"].title,
            "company": r["job"].company,
            "apply_url": r["job"].application_link,
            "score": round(r["score"], 4),
            "seniority_match": r["seniority_match"],
            "experience_bucket": r["experience_bucket"],
        }
        for r in results
    ]

    return JsonResponse({
        "cv_id": cv.id,
        "results": data
    })


# MATCHING – HTML VIEW
def match_jobs_view(request, cv_id):
    try:
        top_n = int(request.GET.get("top", 5))
    except ValueError:
        top_n = 5

    cv = get_object_or_404(CV, id=cv_id)
    results = match_jobs_to_cv(cv.id, top_n)

    return render(request, "jobfinder/match_results.html", {
        "cv": cv,
        "results": results,   # ✅ matches template
        "top": top_n
    })
