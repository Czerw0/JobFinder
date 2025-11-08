from django.db import models
from django.utils import timezone
from datetime import timedelta

class Job(models.Model):
    # Status for long-term management (e.g., hiding jobs older than 3-4 months)
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
    attributes = models.JSONField(null=True, blank=True)
    job_url = models.URLField(unique=True) # unique=True prevents duplicate jobs
    date_posted = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    date_last_seen = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)


    def __str__(self):
        return f"{self.title} at {self.company}"
    
    @property
    def is_potentially_stale(self) -> bool:
        """
        Returns True if the job was last seen in the API feed more than 20 days ago.
        This is used to display a warning to the user.
        """
        if not self.date_last_seen:
            return True # Should not happen, but good to be safe
            
        # The threshold is 20 days ago from the current time.
        stale_threshold = timezone.now() - timedelta(days=20)
        return self.date_last_seen < stale_threshold