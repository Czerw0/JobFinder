from django.db import models

class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, blank=True)
    salary = models.CharField(max_length=100, null=True, blank=True)
    attributes = models.JSONField(null=True, blank=True)
    job_url = models.URLField(unique=True) # unique=True prevents duplicate jobs
    date_posted = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    date_scraped = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company}"