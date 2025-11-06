from django.shortcuts import render
from .models import Job

def home(request):
    return render(request, 'jobfinder/home.html')

def job_list(request):
    jobs = Job.objects.all().order_by('-date_scraped') # Get all jobs, newest first
    return render(request, 'jobfinder/job_list.html', {'jobs': jobs})