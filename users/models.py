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

    # Kontakt
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    github_profile = models.URLField(blank=True)
    linkedin_profile = models.URLField(blank=True)

    # Krytyczne pola dla dopasowywania
    skills = models.TextField(blank=True, default="", help_text="Skills (comma separated).")
    technologies = models.TextField(blank=True, default="", help_text="Technologies (comma separated).")
    preferred_roles = models.TextField(blank=True, default="", help_text="Preferable job roles (comma separated)")
    preferred_locations = models.TextField(blank=True, default="", help_text="Preferable locations (comma separated)")
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

    # Doświadczenie
    experience_years = models.IntegerField(null=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    languages = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CV for {self.user.username if self.user else self.full_name}"
