# users/models.py
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'


class CV(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    # Contact
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    github_profile = models.URLField(blank=True)
    linkedin_profile = models.URLField(blank=True)

    # Matching-critical fields
    skills = models.TextField(blank=True, default="", help_text="Comma-separated skills.")
    technologies = models.TextField(blank=True, default="", help_text="Comma-separated technologies.")
    preferred_roles = models.TextField(blank=True, default="", help_text="Comma-separated preferred roles.")
    preferred_locations = models.TextField(blank=True, default="", help_text="Comma-separated locations.")
    job_seniority = models.CharField(
        max_length=20,
        choices=[('junior','Junior'),('mid','Mid'),('senior','Senior')],
        default='junior',
    )
    job_type_preference = models.CharField(
        max_length=20,
        choices=[('remote','Remote'),('hybrid','Hybrid'),('office','Office')],
        default='remote',
    )
    industry_preference = models.CharField(max_length=100, blank=True, default='')

    # Experience
    experience_years = models.IntegerField(null=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    languages = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CV for {self.user.username if self.user else self.full_name}"
