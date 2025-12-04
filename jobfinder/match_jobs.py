from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from jobfinder.models import Job
from users.models import CV
import pandas as pd
import re

from jobfinder.logging_config import setup_logger
logger = setup_logger("matcher", "matcher.log")


# text normalization function
def normalize_text(text: str) -> str:
    """
    Clean text so TF-IDF works better:
    - lowercase
    - remove non-alphanumeric chars (except + and # common in tech names)
    - strip extra spaces
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9+# ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text



# main matching function
def match_jobs_to_cv(cv_id, top_n=5):
    try:
        cv = CV.objects.get(id=cv_id) # get the CV by ID
    except CV.DoesNotExist:
        logger.error(f"CV with id {cv_id} does not exist.")
        return []

    # Combine all relevant CV fields into one text 
    cv_text = " ".join([
        normalize_text(cv.skills or ""),
        normalize_text(cv.technologies or ""),
        normalize_text(cv.preferred_roles or ""),
        normalize_text(cv.preferred_locations or ""),
        normalize_text(cv.experience or ""),
        normalize_text(cv.education or ""),
        normalize_text(cv.languages or ""),
    ])

    # Fetch active job postings
    jobs = Job.objects.filter(status=Job.STATUS_ACTIVE)
    if not jobs.exists():
        logger.info("No active jobs found for matching.")
        return []

    job_ids = []
    job_links = []
    job_titles = []
    job_tags = []
    job_descs = []

    for job in jobs:
        job_ids.append(job.id)
        job_links.append(job.job_url)
        job_titles.append(normalize_text(job.title or ""))

        # tags from the API → attributes list
        if isinstance(job.attributes, list):
            tag_txt = " ".join([normalize_text(str(t)) for t in job.attributes])
        else:
            tag_txt = ""

        job_tags.append(tag_txt)
        job_descs.append(normalize_text(job.description or ""))

    # DataFrame
    jobs_df = pd.DataFrame({
        "id": job_ids,
        "link": job_links,
        "title": job_titles,
        "tags": job_tags,
        "desc": job_descs,
    })

    # combined text for TF-IDF
    jobs_df["combined_text"] = (
        jobs_df["title"] + " " +
        jobs_df["tags"] + " " +
        jobs_df["desc"]
    )

    # TF-IDF Vectorization best settings
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),       # unigrams + bigrams
        min_df=1,                 # keep all terms
        max_df=0.9,               # ignore extremely common words
    )

    job_vectors = vectorizer.fit_transform(jobs_df["combined_text"])
    cv_vector = vectorizer.transform([cv_text])

    # Cosine similarity
    similarities = cosine_similarity(cv_vector, job_vectors).flatten()
    jobs_df["similarity"] = similarities

    # logging
    for _, row in jobs_df.iterrows():
        logger.debug(
            f"Similarity | Job ID {row['id']} | "
            f"Title: {row['title']} | "
            f"Score: {row['similarity']:.4f}"
        )

    # Top-N
    top_df = jobs_df.nlargest(top_n, "similarity")
    top_ids = top_df["id"].tolist()

    top_jobs = Job.objects.filter(id__in=top_ids)

    # sort by similarity
    top_jobs = sorted(
        top_jobs,
        key=lambda job: float(top_df[top_df["id"] == job.id]["similarity"].values[0]),
        reverse=True
    )

    return top_jobs
