from datetime import timedelta 
from django.utils import timezone
from django.core.management.base import BaseCommand #Wkonanie tego pliku osobno jako komenda zarzadzania
from django.db.models import Q
from jobfinder.models import Job
from jobfinder.logging_config import setup_logger

# Ustawienia loggera
logger = setup_logger("archiver", "archive.log")


class Command(BaseCommand):

    def handle(self, *args, **options):
        # archiwizuj oferty pracy niewidziane/opublikowane od 30 dni
        threshold = timezone.now() - timedelta(days=30)

        self.stdout.write(f"Archiving jobs older than {threshold.isoformat()} ...")

        # Wybierz oferty aktywne, które są starsze niż próg
        qs = Job.objects.filter(
            status=Job.STATUS_ACTIVE
        ).filter(
            Q(date_last_seen__lt=threshold) | Q(date_posted__lt=threshold)
        )

        count = qs.count()

        # Jeśli są jakieś oferty do zarchiwizowania, zaktualizuj ich status
        if count:
            qs.update(status=Job.STATUS_ARCHIVED)
            msg = f"Archived {count} stale jobs."
            logger.info(msg)
            self.stdout.write(self.style.SUCCESS(msg))
        else:
            self.stdout.write(self.style.SUCCESS("No stale jobs found."))



