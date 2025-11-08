import logging
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from jobfinder.models import Job
from datetime import datetime

# Get a logger instance for this module
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Scrapes job offers from the RemoteOK API, cleans the data,
    and saves new or updated job offers to the database.
    """
    help = "Scrapes job offers from the RemoteOK API and saves them to the database."

    API_URL = "https://remoteok.com/api"
    USER_AGENT = "JobFinderApp/1.0 (your-email@example.com)" # It's polite to add a contact email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def handle(self, *args, **options):
        """The main entry point for the Django management command."""
        logger.info(f"Starting job scrape from {self.API_URL}...")

        try:
            job_data = self._fetch_job_data()
            if not job_data:
                logger.warning("No job data returned from API. Halting execution.")
                self.stdout.write(self.style.WARNING("No job data returned from API."))
                return

            logger.info(f"Found {len(job_data)} job offers in API response.")
            new_jobs, updated_jobs = self._process_and_save_jobs(job_data)

            success_message = (
                f"Scraping complete. Added {new_jobs} new jobs, "
                f"updated {updated_jobs} existing ones."
            )
            logger.info(success_message)
            self.stdout.write(self.style.SUCCESS(success_message))

        except requests.exceptions.RequestException as e:
            logger.error(f"Network/API error: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f"Network/API error: {e}"))
        except ValueError as e:
            logger.error(f"JSON decoding error: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f"JSON decoding error: {e}"))
        except Exception as e:
            logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(f"Unexpected error: {type(e).__name__} — {e}"))

    def _fetch_job_data(self) -> list:
        """Fetches and returns job data from the RemoteOK API."""
        response = self.session.get(self.API_URL, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list) and len(data) > 1:
            return data[1:] # Skip the first element which is a legal notice
        return []
    
    def _format_salary(self, offer: dict) -> str:
        """Formats the salary range into a human-readable string."""
        min_sal = offer.get("salary_min")
        max_sal = offer.get("salary_max")

        if min_sal and max_sal:
            return f"${min_sal:,} - ${max_sal:,}"
        if min_sal:
            return f"From ${min_sal:,}"
        if max_sal:
            return f"Up to ${max_sal:,}"
        return "N/A"

    def _process_and_save_jobs(self, job_data: list) -> tuple[int, int]:
        """
        Processes a list of job offers and saves them to the database
        inside a single transaction.
        """
        new_jobs_added = 0
        updated_jobs = 0

        with transaction.atomic():
            for offer in job_data:
                job_url = offer.get("url")
                if not job_url:
                    continue

                # Parse the original posting date from the API
                date_posted_str = offer.get("date")
                date_posted_obj = None
                if date_posted_str:
                    try:
                        # Handles formats like "2025-11-04T00:05:07+00:00"
                        date_posted_obj = datetime.fromisoformat(date_posted_str)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse date: {date_posted_str} for job {job_url}")

                raw_description = offer.get("description", "")
                description_text = BeautifulSoup(raw_description, "html.parser").get_text(separator="\n").strip()

                attributes = offer.get("tags", [])
                if isinstance(attributes, str):
                    attributes = [attributes]

                job_defaults = {
                    "title": offer.get("position", "Untitled"),
                    "company": offer.get("company", "Unknown Company"),
                    "location": offer.get("location", "Remote"),
                    "attributes": attributes,
                    "salary": self._format_salary(offer),
                    "description": description_text,
                    "date_posted": date_posted_obj, 
                    "status": Job.STATUS_ACTIVE, # IMPORTANT: Always set status to active when seen
                }

                _, created = Job.objects.update_or_create(
                    job_url=job_url,
                    defaults=job_defaults,
                )

                if created:
                    new_jobs_added += 1
                else:
                    updated_jobs += 1

        return new_jobs_added, updated_jobs