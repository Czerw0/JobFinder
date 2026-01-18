from django.db import models 
from django.utils import timezone
from datetime import timedelta

class Job(models.Model):
    # use these statuses to manage job visibility over time
    # Active jobs are shown to users, archived ones are hidden (usually after 3-4 months)
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
    attributes = models.JSONField(null=True, blank=True) # store job tags/attributes as JSON
    job_url = models.URLField(unique=True)  # Prevent duplicate job postings
    date_posted = models.DateTimeField(null=True, blank=True) 
    description = models.TextField(null=True, blank=True)
    date_last_seen = models.DateTimeField(auto_now=True)  # Updated whenever see the job in our feed
    match_score = models.FloatField(null=True, blank=True)  # Store last computed match score

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    def __str__(self):
        return f"{self.title} at {self.company}"
    
    @property # indicates this is accessed like an attribute
    def is_potentially_stale(self) -> bool:
        """
        Check if a job listing looks outdated. We flag jobs that haven't appeared
        in our API feed for more than 30 days, so users know it might no longer be available.
        """
        if not self.date_last_seen:
            return True  # Safety check - treat missing dates as stale

        # Mark as stale if haven't seen it in the last 30 days
        stale_threshold = timezone.now() - timedelta(days=30)
        return self.date_last_seen < stale_threshold