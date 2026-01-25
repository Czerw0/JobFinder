import requests # for making HTTP requests
from bs4 import BeautifulSoup # for parsing HTML content
from django.core.management.base import BaseCommand # base class for management commands
from django.db import transaction # for atomic database transactions
from jobfinder.models import Job
from datetime import datetime # for handling date and time
from jobfinder.logging_config import setup_logger # custom logger setup
from django.utils import timezone

logger = setup_logger("scraper", "scraper.log")


class Command(BaseCommand):

    API_URL = "https://remoteok.com/api"
    USER_AGENT = "JobFinderApp/1.0 (kczerwinski3@st.swps.edu.pl)"

    # Main entry point for the command
    def handle(self, *args, **options):
        logger.info("Starting job scrape...")

        try:
            jobs = self._fetch_jobs()
            if not jobs:
                self.stdout.write(self.style.WARNING("No job data returned."))
                return

            new_count, update_count = self._save_jobs(jobs)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Done. Added {new_count} new jobs, updated {update_count}."
                )
            )

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(str(e)))

    # Reach out to the RemoteOK API and return the parsed JSON list (skip the first meta item).

    def _fetch_jobs(self):
        session = requests.Session()
        session.headers.update({"User-Agent": self.USER_AGENT})

        r = session.get(self.API_URL, timeout=20)
        r.raise_for_status()
        data = r.json()

        return data[1:] if isinstance(data, list) and len(data) > 1 else []

    # Insert or update job records in the database
    def _save_jobs(self, data):
        new_jobs = 0
        updated_jobs = 0

        with transaction.atomic():  #all or nothing 
            for offer in data:
                url = offer.get("url")
                if not url:
                    continue

                # Try to parse the ISO-format date the API gives us; use None if it's missing or miread.
                date_str = offer.get("date")
                try:
                    posted_date = datetime.fromisoformat(date_str) if date_str else None
                except ValueError:
                    posted_date = None

                # Remove any HTML from the job description but keep line breaks where appropriate.
                import ftfy

                # Pobierasz surowy opis
                raw_description = offer.get("description", "")

                # 1. Naprawiasz błędy kodowania (np. zamiana u00c2\u00ae na ®)
                clean_description = ftfy.fix_text(raw_description)

                # 2. Parsujesz naprawiony tekst przez BeautifulSoup
                description = BeautifulSoup(
                    clean_description, "html.parser"
                ).get_text(separator="\n").strip()

                # Ensure tags are represented as a list so we can store them consistently.
                tags = offer.get("tags", [])
                if isinstance(tags, str):
                    tags = [tags]

                # Create a human-readable salary string from min/max values if available.
                sal_min = offer.get("salary_min")
                sal_max = offer.get("salary_max")
                if sal_min and sal_max:
                    salary = f"${sal_min:,} - ${sal_max:,}"
                elif sal_min:
                    salary = f"From ${sal_min:,}"
                elif sal_max:
                    salary = f"Up to ${sal_max:,}"
                else:
                    salary = "N/A"

                defaults = {
                    "title": offer.get("position", "Untitled"),
                    "company": offer.get("company", "Unknown Company"),
                    "location": offer.get("location", "Remote"),
                    "attributes": tags,
                    "salary": salary,
                    "description": description,
                    "date_posted": posted_date,
                    "status": Job.STATUS_ACTIVE,
                }

                job, created = Job.objects.update_or_create(
                    job_url=url,
                    defaults=defaults
                )

                # when creating/updating job objects set date_last_seen = timezone.now()
                job.date_last_seen = timezone.now()
                job.save()

                new_jobs += int(created)
                updated_jobs += int(not created)

        logger.info("Scraper run completed: %s new, %s updated", new_jobs, updated_jobs)

        return new_jobs, updated_jobs
