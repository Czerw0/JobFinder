from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users' 

urlpatterns = [
    path('register/', views.register, name='register'),
    # Django's built-in views handle the logic for login and logout
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('cv/', views.view_cv, name='view_cv'),
    path('cv/manage/', views.manage_cv, name='manage_cv'),
]