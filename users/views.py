from django.shortcuts import render, redirect
from django.contrib import messages 
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, CVForm
from .models import CV


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

@login_required
def view_cv(request):
    try:
        cv = request.user.cv
    except CV.DoesNotExist:
        cv = None
    return render(request, 'users/view_cv.html', {'cv': cv})

@login_required
def manage_cv(request):
    try:
        cv_instance = request.user.cv
    except CV.DoesNotExist:
        cv_instance = None

    if request.method == 'POST':
        # Pass the instance if it exists, otherwise it's a new form
        form = CVForm(request.POST, instance=cv_instance)
        if form.is_valid():
            new_cv = form.save(commit=False)
            # Assign the current user to the cv
            new_cv.user = request.user
            new_cv.save()
            messages.success(request, 'Your CV has been updated!')
            return redirect('users:view_cv')
    else:
        # On a GET request, show the form pre-filled with existing data
        form = CVForm(instance=cv_instance)

    return render(request, 'users/manage_cv.html', {'form': form})
