from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db.models import Q
from jobfinder.models import Job
from jobfinder.logging_config import setup_logger

logger = setup_logger("deleter", "delete.log")


# Komenda do usuwania starych zarchiwizowanych ofert pracy
class Command(BaseCommand):
    
    # Metoda obsługująca komendę
    def handle(self, *args, **options):
        # Ustaw próg usunięcia na 35 dni temu
        delete_threshold = timezone.now() - timedelta(days=35)
        # Wyszukaj zarchiwizowane oferty starsze niż próg
        self.stdout.write(f"Searching for archived jobs with date < {delete_threshold.isoformat()} ...")

        # Zapytanie do bazy danych dla zarchiwizowanych ofert
        qs = Job.objects.filter(
            status=Job.STATUS_ARCHIVED
        ).filter(
            Q(date_last_seen__lt=delete_threshold) | Q(date_posted__lt=delete_threshold)
        )

        # Liczba znalezionych ofert
        count = qs.count()

        # Jeśli znaleziono oferty, usuń je
        if count:
            logger.info("Deleting %s archived jobs older than %s", count, delete_threshold.isoformat())
            qs.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} stale jobs."))
        else:
            self.stdout.write(self.style.SUCCESS("No jobs deleted."))
