# JobFinder

A web application for browsing remote job listings with CV-based job matching powered by NLP.

> ⚠️ **Note:** The application fetched job listings from the [RemoteOK](https://remoteok.com/api) API. Due to changes in the API structure, live job fetching is currently unavailable. The source code and matching algorithm are fully functional and can be run locally after adapting to a new data source.

---

## Features

- User registration and login
- Browse and filter job listings (by title, location, tags, remote preference)
- Create and edit a structured CV form
- Automatic CV-to-job matching algorithm (NLP: TF-IDF + cosine similarity)
- Job archiving after 30 days of inactivity
- Automatic deletion of jobs older than 35 days
- Django admin panel
- Event logging to files (scraper, archiver, matcher, deleter)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 5.2 |
| Frontend | HTML, CSS, Bootstrap 5 |
| Database | PostgreSQL |
| NLP / ML | scikit-learn (TF-IDF, cosine similarity) |
| HTML Parsing | BeautifulSoup4, ftfy |
| Configuration | django-environ, python-dotenv |

---

## Project Structure

```
JobFinder/
├── job_matcher/          # Main Django configuration folder
│   ├── settings.py       # Project settings, database, logging config
│   ├── urls.py           # Project-level URL routing
│   ├── wsgi.py
│   └── asgi.py
│
├── jobfinder/            # App: job listings, API integration, matching algorithm
│   ├── management/
│   │   └── commands/
│   │       ├── scrape_remotejobs.py   # Fetch jobs from RemoteOK API
│   │       ├── archive_old_jobs.py    # Archive jobs unseen for 30+ days
│   │       └── delete_stale_jobs.py   # Delete jobs older than 35 days
│   ├── templates/jobfinder/
│   │   ├── home.html
│   │   ├── job_list.html             # Job listing + filtering view
│   │   └── match_results.html        # Matched jobs view
│   ├── static/jobfinder/css/
│   │   └── jobs.css
│   ├── models.py         # Job model
│   ├── views.py          # Views: home, job_list, match_jobs
│   ├── match_jobs.py     # CV ↔ job matching algorithm
│   ├── logging_config.py # Logger setup
│   ├── inspect_api.py    # Helper script for API structure inspection
│   └── urls.py
│
├── users/                # App: user accounts and CV
│   ├── templates/
│   │   ├── base.html
│   │   └── users/
│   │       ├── login.html
│   │       ├── logout.html
│   │       ├── register.html
│   │       ├── view_cv.html
│   │       └── manage_cv.html
│   ├── models.py         # Models: Profile, CV
│   ├── forms.py          # Forms: UserRegistrationForm, CVForm
│   ├── views.py          # Views: register, view_cv, manage_cv
│   ├── context_processors.py
│   └── urls.py
│
├── logs/                 # Log files (auto-generated)
│   ├── scraper.log
│   ├── archive.log
│   ├── matcher.log
│   └── delete.log
│
├── .env                  # Environment variables (do NOT commit!)
├── .gitignore
├── manage.py
└── requirements.txt
```

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Czerw0/JobFinder.git
cd JobFinder
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the `.env` file

Create a `.env` file in the root directory (next to `manage.py`) with the following content:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

> Make sure PostgreSQL is running and accessible with the credentials above.

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. (Optional) Create an admin account

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

The application will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Management Commands

These commands can be run manually from the terminal:

```bash
# Fetch job listings from the RemoteOK API
python manage.py scrape_remotejobs

# Archive jobs not seen for more than 30 days
python manage.py archive_old_jobs

# Delete archived jobs older than 35 days
python manage.py delete_stale_jobs
```

> In the current version, these commands are triggered automatically every time a user visits the job listing page.

---

## Matching Algorithm

The algorithm in `jobfinder/match_jobs.py` works as follows:

1. Fetches the logged-in user's CV from the database.
2. Fetches all active job listings.
3. Vectorizes job and CV texts using **TF-IDF** (scikit-learn).
4. Computes **cosine similarity** between the CV and each job listing.
5. Adjusts a base score (0.35) based on additional factors:
   - skill and technology matches against job tags
   - seniority level (junior / mid / senior)
   - required years of experience
   - preferred roles and location
6. Normalizes the final score to a 0–100% range.
7. Returns the top 5 best-matched job listings.

---

## Requirements

Full list of dependencies in `requirements.txt`:

```
Django==5.2.8
django-environ==0.12.0
python-dotenv==1.2.1
requests==2.32.5
beautifulsoup4==4.14.2
scikit-learn==1.7.2
psycopg2-binary==2.9.11
ftfy==6.3.1
django-crontab==0.7.1
pandas==2.3.3
```

---

## Security

- Passwords hashed by Django (PBKDF2)
- Views protected with the `@login_required` decorator
- SQL injection protection via Django ORM
- CSRF protection via form tokens
- Clickjacking protection via Django middleware
- Sensitive data stored in `.env`, excluded from the repository via `.gitignore`
- `DEBUG=False` in production

---

## Potential Future Improvements

- Automated job refresh via cron / Celery instead of triggering on every page load
- Support for additional job data sources (more APIs)
- Extended user profile: activity history, saved jobs, multiple CV variants
- Recruiter module for posting job listings
- Email notifications
- HTTPS, login rate limiting, two-factor authentication
- Matching algorithm improvements

---

## Author

**Karol Czerwiński**  
Academic project — SWPS, 2025/2026
