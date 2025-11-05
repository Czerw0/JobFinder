from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import CV

#Django will handle the password automaticly in UserCreationForm
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username','email']

#Form for CV model
class CVForm(forms.ModelForm):
    class Meta:
        model = CV
        fields = ['full_name', 'email', 'phone_number', 'github_profile', 
                  'linkedin_profile', 'skills', 'experience', 'education', 'languages']