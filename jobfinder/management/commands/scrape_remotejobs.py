import logging
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from jobfinder.models import Job
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scrapes job offers from RemoteOK and saves them to the database."

    API_URL = "https://remoteok.com/api"
    USER_AGENT = "JobFinderApp/1.0 (kczerwinski3@st.swps.edu.pl)"

    # ------------------ FETCH ------------------ #

    def _fetch_jobs(self):
        session = requests.Session()
        session.headers.update({"User-Agent": self.USER_AGENT})

        r = session.get(self.API_URL, timeout=20)
        r.raise_for_status()
        data = r.json()

        return data[1:] if isinstance(data, list) and len(data) > 1 else []

    # ------------------ SAVE ------------------ #

    def _save_jobs(self, data):
        new_jobs = 0
        updated_jobs = 0

        with transaction.atomic():
            for offer in data:
                url = offer.get("url")
                if not url:
                    continue

                # Parse date
                date_str = offer.get("date")
                try:
                    posted_date = datetime.fromisoformat(date_str) if date_str else None
                except ValueError:
                    posted_date = None

                # Clean description
                description = BeautifulSoup(
                    offer.get("description", ""), "html.parser"
                ).get_text(separator="\n").strip()

                # Normalize tags
                tags = offer.get("tags", [])
                if isinstance(tags, str):
                    tags = [tags]

                # Salary formatting (simplified)
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

                _, created = Job.objects.update_or_create(
                    job_url=url,
                    defaults=defaults
                )

                new_jobs += int(created)
                updated_jobs += int(not created)

        return new_jobs, updated_jobs
