import requests # do wykonywania żądań HTTP
from bs4 import BeautifulSoup # do parsowania zawartości HTML
import ftfy # do parsowania zawartości HTML
from django.core.management.base import BaseCommand # klasa bazowa dla komend zarządzania
from django.db import transaction # do atomowych transakcji bazy danych
from jobfinder.models import Job
from datetime import datetime # do obsługi daty i czasu
from jobfinder.logging_config import setup_logger # własne ustawienia loggera
from django.utils import timezone

logger = setup_logger("scraper", "scraper.log")


class Command(BaseCommand):

    API_URL = "https://remoteok.com/api"
    USER_AGENT = "JobFinderApp/1.0"

    # Główny punkt wejścia dla komendy
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

    # Skontaktuj się z API RemoteOK i zwróć sparsowaną listę JSON (pomiń pierwszy element meta).

    def _fetch_jobs(self):
        session = requests.Session()
        session.headers.update({"User-Agent": self.USER_AGENT})

        r = session.get(self.API_URL, timeout=20)
        r.raise_for_status()
        data = r.json()

        return data[1:] if isinstance(data, list) and len(data) > 1 else []

    # Wstaw lub zaktualizuj rekordy ofert pracy w bazie danych
    def _save_jobs(self, data):
        new_jobs = 0
        updated_jobs = 0

        with transaction.atomic():  # wszystko albo nic 
            for offer in data:
                url = offer.get("url")
                if not url:
                    continue

                # Spróbuj sparsować datę w formacie ISO podaną przez API; użyj None jeśli brakuje lub jest błędna.
                date_str = offer.get("date")
                try:
                    posted_date = datetime.fromisoformat(date_str) if date_str else None
                except ValueError:
                    posted_date = None

                

                # Czyszczenie HTML w opisie oferty pracy
                raw_description = offer.get("description", "")
                clean_description = ftfy.fix_text(raw_description)
                description = BeautifulSoup(
                    clean_description, "html.parser"
                ).get_text(separator="\n").strip()

                # Upewnij się, że tagi są reprezentowane jako lista, aby przechowywać je konsekwentnie.
                tags = offer.get("tags", [])
                if isinstance(tags, str):
                    tags = [tags]

                # Utwórz czytelny  string wynagrodzenia z wartości min/max jeśli dostępne.
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

                # podczas tworzenia/aktualizacji obiektów ofert ustaw date_last_seen = timezone.now()
                job.date_last_seen = timezone.now()
                job.save()

                new_jobs += int(created)
                updated_jobs += int(not created)

        logger.info("Scraper run completed: %s new, %s updated", new_jobs, updated_jobs)

        return new_jobs, updated_jobs
