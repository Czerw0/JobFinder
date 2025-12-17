# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CV

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']

class CVForm(forms.ModelForm):
    class Meta:
        model = CV
        fields = [
            'full_name', 'email', 'phone_number', 'github_profile', 'linkedin_profile',
            'skills', 'technologies', 'preferred_roles', 'preferred_locations',
            'job_seniority', 'job_type_preference', 'industry_preference',
            'experience_years', 'experience', 'education', 'languages',
        ]
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3}),
            'technologies': forms.Textarea(attrs={'rows': 2}),
            'preferred_roles': forms.Textarea(attrs={'rows': 2}),
            'preferred_locations': forms.Textarea(attrs={'rows': 2}),
            'experience': forms.Textarea(attrs={'rows': 5}),
            'education': forms.Textarea(attrs={'rows': 4}),
            'languages': forms.Textarea(attrs={'rows': 2}),
        }
