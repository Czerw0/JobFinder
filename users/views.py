from django.shortcuts import render, redirect
from django.contrib import messages 
from .forms import UserRegistrationForm

'''
This method handles user registration. It takes blank form and if the form is valid,
it saves the data and creates user. After that it takes user to the login page.
'''
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save() #Saves the user 
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login') #Redirect to login page after successful registration
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})
