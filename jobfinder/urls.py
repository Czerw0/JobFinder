from django.urls import path, include
from .import views

app_name = 'jobfinder'

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
]