# In jobfinder/management/commands/scrape_remoteok.py

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from jobfinder.models import Job

class Command(BaseCommand):
    help = 'Scrapes job offers from the RemoteOK API and saves them to the database'

    def handle(self, *args, **options):
        # The official, public API endpoint for RemoteOK
        API_URL = "https://remoteok.com/api"

        self.stdout.write(self.style.SUCCESS(f"Starting to fetch job offers from {API_URL}..."))

        try:
            # Add a User-Agent header, which is good practice for any API call
            headers = {
                'User-Agent': 'JobFinderApp/1.0 (karol.czerwinski@student.swps.edu.pl)'
            }
            response = requests.get(API_URL, headers=headers)
            response.raise_for_status() # Check for errors (4xx or 5xx)

            # The RemoteOK API returns a list of dictionaries (JSON)
            # The first item in the list is a legal notice, so we skip it with [1:]
            job_data = response.json()[1:]

            if not job_data:
                self.stdout.write(self.style.WARNING("API returned no job data."))
                return

            self.stdout.write(f"Found {len(job_data)} job offers.")
            new_jobs_added = 0

            for offer in job_data:
                # Map the API's field names to our Job model's field names
                title = offer.get('position')
                company = offer.get('company')
                # The 'location' field is often empty for remote jobs, so we provide a default
                location = offer.get('location', 'Remote')
                job_url = offer.get('url')

                # Skip this offer if it's a sponsored post without a real URL
                if not job_url:
                    continue

                # Construct a salary string if salary data is available
                min_sal = offer.get('salary_min')
                max_sal = offer.get('salary_max')
                salary_str = "N/A"
                if min_sal and max_sal:
                    salary_str = f"${min_sal:,} - ${max_sal:,}" # Format with commas

                # The description comes as HTML, so we use BeautifulSoup to get clean text
                description_html = offer.get('description', '')
                soup = BeautifulSoup(description_html, 'html.parser')
                description_text = soup.get_text(separator='\n').strip()

                # Save to our database, avoiding duplicates based on the URL
                job, created = Job.objects.get_or_create(
                    job_url=job_url,
                    defaults={
                        'title': title,
                        'company': company,
                        'location': location,
                        'salary': salary_str,
                        'description': description_text,
                    }
                )

                if created:
                    new_jobs_added += 1

            self.stdout.write(self.style.SUCCESS(f"Scraping complete. Added {new_jobs_added} new jobs."))

        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"An error occurred while fetching the data: {e}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An unexpected error occurred: {e}"))