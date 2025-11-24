from django import forms # import Django's form library
from django.contrib.auth.models import User # import the User model
from django.contrib.auth.forms import UserCreationForm # import the user creation form
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
        fields = [
            'full_name', 'email', 'phone_number', 'github_profile',
            'linkedin_profile', 'skills', 'experience_years',
            'experience', 'education', 'languages'
        ]
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3}),
            'experience': forms.Textarea(attrs={'rows': 5}),
            'education': forms.Textarea(attrs={'rows': 4}),
            'languages': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_experience_years(self):
        years = self.cleaned_data.get('experience_years')
        if years is None:
            return years
        if years < 0:
            raise forms.ValidationError("Experience years cannot be negative.")
        return years