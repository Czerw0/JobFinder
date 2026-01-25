from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.management import call_command
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
    Pokazuje wszystkie aktywne oferty pracy.
    Odświeża i archiwizuje przy każdym żądaniu.
    """

    # Odśwież oferty
    try:
        call_command("scrape_remotejobs")
    except Exception as e:
        print(f"Scraping error: {e}")

    #Archiwizuj przestarzałe oferty 
    try:
        # wywołaj komendę zarządzania zaimplementowaną w archive_old_jobs.py
        call_command("archive_old_jobs")
    except Exception as e:
        print(f"Archiving error: {e}")
    
    #Usuń przestarzałe oferty
    try:
        call_command("delete_stale_jobs")
    except Exception as e:
        print(f"Deleting error: {e}")

    #Zapytanie o aktywne oferty
    queryset = Job.objects.filter(status=Job.STATUS_ACTIVE)

    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(Q(title__icontains=q))

    location = request.GET.get('location', '').strip().lower()
    if location:
        queryset = queryset.filter(location__icontains=location)

    tags = []
    tags += request.GET.getlist('tag')
    tags_param = request.GET.get('tags', '')
    if tags_param:
        tags += [t.strip() for t in tags_param.split(',') if t.strip()]

    if tags:
        tags_q = Q()
        for t in tags:
            tags_q |= Q(attributes__contains=[t])
        queryset = queryset.filter(tags_q)

    remote = request.GET.get('remote', '').strip().lower()
    if remote in ('1', 'true', 'yes', 'remote', 'only'):
        queryset = queryset.filter(
            Q(location__icontains='remote') | Q(attributes__contains=['remote'])
        )
    elif remote in ('0', 'false', 'no', 'onsite'):
        queryset = queryset.exclude(
            Q(location__icontains='remote') | Q(attributes__contains=['remote'])
        )

    jobs = queryset.order_by('-date_last_seen')

    filter_params = {
        'q': q,
        'location': location,
        'tags': ",".join(tags),
        'remote': remote,
    }

    return render(request, 'jobfinder/job_list.html', {
        'jobs': jobs,
        'filter_params': filter_params
    })



# DOPASOWANIE – JSON API
@require_GET
def match_jobs(request, cv_id):
    """
    Punkt końcowy API zwracający rankingowane oferty z wynikami.
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


# DOPASOWANIE – WIDOK HTML
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
    Widok pokazujący oferty pracy pasujące do danego CV.
    """

    cv = get_object_or_404(CV, id=cv_id)
    results = match_jobs_to_cv(cv.id, top_n=1000)  # get all matches

    matched_job_ids = [r["job"].id for r in results]
    jobs = Job.objects.filter(id__in=matched_job_ids, status=Job.STATUS_ACTIVE)

    return render(request, 'jobfinder/job_list.html', {
        'jobs': jobs,
        'filter_cv': cv
    })