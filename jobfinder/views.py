from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import threading
from django.db.models import Q

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

    # Build base queryset
    queryset = Job.objects.filter(status=Job.STATUS_ACTIVE)

    # --- Filtering parameters ---
    # Simple text search over title/company/description
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
        )

    # Location filter (partial match)
    location = request.GET.get('location', '').strip().lower()
    if location:
        queryset = queryset.filter(location__icontains=location)

    # Tags (attributes) filter - allow ?tag=python&tag=django or ?tags=python,django
    tags = []
    # multiple repeated params: ?tag=python&tag=django
    tags += request.GET.getlist('tag')
    # comma-separated param: ?tags=python,django
    tags_param = request.GET.get('tags', '')
    if tags_param:
        tags += [t.strip() for t in tags_param.split(',') if t.strip()]

    if tags:
        tags_q = Q()
        for t in tags:
            # attributes is stored as a JSON list; use contains to find element
            tags_q |= Q(attributes__contains=[t])
        queryset = queryset.filter(tags_q)

    # Remote filter: ?remote=remote  (only remote), ?remote=onsite (exclude remote)
    remote = request.GET.get('remote', '').strip().lower()
    if remote in ('1', 'true', 'yes', 'remote', 'only'):
        queryset = queryset.filter(
            Q(location__icontains='remote') | Q(attributes__contains=['remote'])
        )
    elif remote in ('0', 'false', 'no', 'onsite'):
        queryset = queryset.exclude(
            Q(location__icontains='remote') | Q(attributes__contains=['remote'])
        )

    # Final ordering
    jobs = queryset.order_by('-date_last_seen')

    # Pass current filter params to template for pre-filling the form
    filter_params = {
        'q': q,
        'location': location,
        'tags': ",".join(tags),
        'remote': remote,
    }

    return render(request, 'jobfinder/job_list.html', {'jobs': jobs, 'filter_params': filter_params})


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
    cv = get_object_or_404(CV, id=cv_id)
    top = int(request.GET.get("top", 5))
    results = match_jobs_to_cv(cv_id, top_n=top) or []

    # add percent-friendly value for template
    for r in results:
        try:
            r["score_pct"] = round(float(r.get("score", 0)) * 100, 2)
        except Exception:
            r["score_pct"] = None

    return render(request, "jobfinder/match_results.html", {
        "cv": cv,
        "results": results,
        "top": top,
    })


def filter(request, cv_id):
    """
    View showing jobs that match a given CV.
    """

    cv = get_object_or_404(CV, id=cv_id)
    results = match_jobs_to_cv(cv.id, top_n=1000)  # get all matches

    matched_job_ids = [r["job"].id for r in results]
    jobs = Job.objects.filter(id__in=matched_job_ids, status=Job.STATUS_ACTIVE)

    return render(request, 'jobfinder/job_list.html', {
        'jobs': jobs,
        'filter_cv': cv
    })