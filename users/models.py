from django.db import models
from django.contrib.auth.models import User

# This is the model for additional user profile information.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)


    def __str__(self):
        return f'{self.user.username} Profile'

# This is the model for the CV form data.
class CV(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    github_profile = models.URLField(blank=True)
    linkedin_profile = models.URLField(blank=True)
    skills = models.TextField(help_text="Enter skills separated by commas")
    experience_years= models.IntegerField(help_text="Number of years of experience in field", default=None, null=True, blank=True)
    experience = models.TextField(help_text="Describe your work experience.")
    education = models.TextField(help_text="Describe your education.")
    languages = models.TextField(help_text="List languages you know, separated by commas.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'CV for {self.user.username}'