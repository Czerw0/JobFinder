from django.shortcuts import render
from .models import Job
from django.core.management import call_command
import threading


def home(request):
    return render(request, 'jobfinder/home.html')

def job_list(request):

    def refresh_api():
        print("Refreshing jobs...")
        try:
            call_command('scrape_remotejobs')
            print("Scraping command finished.")
        except Exception as e:
            print(f"An error occurred while refreshing the api: {e}")


    scraper_thread = threading.Thread(target=refresh_api)
    scraper_thread.start()
    jobs = Job.objects.all().order_by('-date_scraped')
    return render(request, 'jobfinder/job_list.html', {'jobs': jobs})

