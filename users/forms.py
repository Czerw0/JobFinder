from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

#Django will handle the password automaticly in UserCreationForm
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username','email']