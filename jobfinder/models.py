from django.db import models 
from django.utils import timezone
from datetime import timedelta

class Job(models.Model):
    # użyj tych statusów do zarządzania widocznością ofert pracy w czasie
    # Aktywne oferty są pokazywane użytkownikom, zarchiwizowane są ukryte (zwykle po 3-4 miesiącach)
    STATUS_ACTIVE = 'active'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ARCHIVED, 'Archived'),
    ]
    
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, blank=True)
    salary = models.CharField(max_length=100, null=True, blank=True)
    attributes = models.JSONField(null=True, blank=True) # przechowuj tagi/atrybuty oferty jako JSON
    job_url = models.URLField(unique=True)  # Zapobiegaj duplikatom ogłoszeń o pracę
    date_posted = models.DateTimeField(null=True, blank=True) 
    description = models.TextField(null=True, blank=True)
    date_last_seen = models.DateTimeField(auto_now=True)  # Aktualizowany za każdym razem, gdy widzimy ofertę w naszym kanale
    match_score = models.FloatField(null=True, blank=True)  # Przechowuj ostatnio obliczony wynik dopasowania

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    def __str__(self):
        return f"{self.title} at {self.company}"
    
    @property # wskazuje, że jest to dostępne jak atrybut
    def is_potentially_stale(self) -> bool:
        """
        Sprawdź, czy ogłoszenie o pracę wygląda na przestarzałe. Oznaczamy oferty, które nie pojawiły się
        w naszym kanale API przez więcej niż 30 dni, aby użytkownicy wiedzieli, że może już nie być dostępne.
        """
        if not self.date_last_seen:
            return True  # Sprawdzenie bezpieczeństwa - traktuj brakujące daty jako przestarzałe

        # Oznacz jako przestarzałe, jeśli nie widziano przez ostatnie 30 dni
        stale_threshold = timezone.now() - timedelta(days=30)
        return self.date_last_seen < stale_threshold