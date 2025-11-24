from sklearn.feature_extraction.text import TfidfVectorizer # for text vectorization
from sklearn.metrics.pairwise import cosine_similarity # for similarity calculation
from jobfinder.models import Job 
from users.models import CV
import pandas as pd 
from jobfinder.logging_config import setup_logger # custom logger setup

# Set up a logger for tracking the matching process
logger = setup_logger("matcher", "matcher.log")

def match_jobs_to_cv(cv_id, top_n=5):
    # Attempt to retrieve the CV by its ID
    # top_n specifies how many top matching jobs to return
    try:
        cv = CV.objects.get(id=cv_id)
    except CV.DoesNotExist:
        logger.error(f"CV with id {cv_id} does not exist.")
        return []

    # Combine relevant CV fields into a single text string for matching
    cv_text = " ".join([
        cv.full_name or "",
        cv.skills or "",
        cv.experience or "",
        cv.education or "",
        cv.languages or "",
    ])

    # Fetch active job postings from the database
    jobs = Job.objects.filter(status=Job.STATUS_ACTIVE)
    if not jobs.exists():
        logger.info("No active jobs found for matching.")
        return []

    # Initialize lists to hold job details
    job_ids = []
    job_links = []
    job_titles = []
    job_tags = []

    # Loop through each job to extract relevant information
    for job in jobs:
        job_ids.append(job.id)
        job_links.append(job.job_url) # job_url is a field in Job model 
        job_titles.append(job.title or "") 

        # Process job attributes to create a tag string
        attrs = job.attributes
        if isinstance(attrs, list):
            tag_text = " ".join([str(x) for x in attrs])
        else:
            tag_text = ""

        job_tags.append(tag_text)

    # Create a DataFrame to hold job information
    jobs_df = pd.DataFrame({
        "id": job_ids,
        "link": job_links,
        "title": job_titles,
        "tags": job_tags,
    })

    # Combine job titles and tags into a single text column for vectorization
    jobs_df["combined_text"] = (
        jobs_df["title"] + " " +
        jobs_df["tags"]
    )

    # Vectorize the combined text using TF-IDF
    vectorizer = TfidfVectorizer(stop_words=None)
    job_vectors = vectorizer.fit_transform(jobs_df["combined_text"])
    cv_vector = vectorizer.transform([cv_text])

    # Calculate cosine similarity between the CV and job postings
    similarities = cosine_similarity(cv_vector, job_vectors).flatten()
    jobs_df["similarity"] = similarities

    # LOG SIMILARITY SCORES HERE 
    for _, row in jobs_df.iterrows():
        logger.debug(
            f"Similarity | Job ID {row['id']} | "
            f"Title: {row['title']} | "
            f"Score: {row['similarity']:.4f}"
        )
    #

    # Retrieve the top N jobs based on similarity scores
    top_jobs_df = jobs_df.nlargest(top_n, "similarity")
    top_ids = top_jobs_df["id"].tolist()

    # Fetch the top jobs from the database
    top_jobs = Job.objects.filter(id__in=top_ids)

    # Sort the top jobs by their similarity scores in descending order
    top_jobs = sorted(
        top_jobs,
        key=lambda job: float(top_jobs_df[top_jobs_df["id"] == job.id]["similarity"].values[0]),
        reverse=True
    )

    return top_jobs
