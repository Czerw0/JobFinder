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
    # keep letters, numbers, +, # and spaces
    text = re.sub(r"[^a-z0-9+# ]+", " ", text)
    # collapse spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text



# main matching function
def match_jobs_to_cv(cv_id, top_n=5):
    try:
        # fetch cv from db
        cv = CV.objects.get(id=cv_id)
    except CV.DoesNotExist:
        logger.error(f"CV with id {cv_id} does not exist.")
        return []

    #  helpers 
    # split normalized space-separated words into set
    def split_set(text):
        return set(t.strip() for t in normalize_text(text).split() if t.strip())

    # infer allowed seniority levels from years of experience
    def infer_allowed_seniority(years: int):
        if years is None:
            return {"junior", "mid"}
        if years < 2:
            return {"intern", "junior"}
        if years < 3:
            return {"junior"}
        if years < 5:
            return {"mid"}
        return {"senior"}

    # mapping of keywords to seniority buckets
    SENIORITY_KEYWORDS = {
        "intern": {"intern", "internship", "trainee"},
        "junior": {"junior", "jr", "associate", "entry", "graduate"},
        "mid": {"mid", "intermediate", "regular"},
        "senior": {"senior", "sr", "lead", "principal", "staff"},
    }

    # detect seniority mentioned in job text
    def detect_job_seniority(text):
        found = set()
        for level, keys in SENIORITY_KEYWORDS.items():
            for k in keys:
                if k in text:
                    found.add(level)
        # fallback if nothing found
        return found or {"junior", "mid"}  # fallback

    #  CV text 
    # combine important CV fields into one text
    cv_text = " ".join([
        normalize_text(cv.skills),
        normalize_text(cv.technologies),
        normalize_text(cv.preferred_roles),
        normalize_text(cv.experience),
        normalize_text(cv.education),
    ])

    # sets for quick matching
    cv_skills = split_set(cv.skills)
    cv_tech = split_set(cv.technologies)
    cv_roles = split_set(cv.preferred_roles)
    cv_locations = split_set(cv.preferred_locations)
    allowed_seniority = infer_allowed_seniority(cv.experience_years)

    jobs = Job.objects.filter(status=Job.STATUS_ACTIVE)
    if not jobs.exists():
        return []

    records = []

    for job in jobs:
        # normalize fields
        title = normalize_text(job.title or job.position or "")
        desc = normalize_text(job.description or "")
        # attributes may be list, join into text
        tags = " ".join(normalize_text(str(t)) for t in job.attributes) if isinstance(job.attributes, list) else ""
        combined = f"{title} {tags} {desc}"

        job_seniority = detect_job_seniority(combined)

        records.append({
            "id": job.id,
            "job": job,
            "text": combined,
            "title": title,
            "seniority": job_seniority,
            "location": normalize_text(job.location or ""),
            "salary_min": job.salary,
            "salary_max": job.salary,
        })

    # TF-IDF
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_df=0.9,
        min_df=1,
    )

    # fit on job texts
    job_vectors = vectorizer.fit_transform(r["text"] for r in records)
    # transform single CV text
    cv_vector = vectorizer.transform([cv_text])
    similarities = cosine_similarity(cv_vector, job_vectors).flatten()

    # scoring 
    scored = []

    for idx, rec in enumerate(records):
        # base score from semantic similarity
        score = float(similarities[idx]) * 0.70

        text_set = split_set(rec["text"])
        # small boosts for exact skill/tech matches
        score += 0.05 * len(cv_skills & text_set)
        score += 0.05 * len(cv_tech & text_set)

        # boost if role appears in job title
        if any(role in rec["title"] for role in cv_roles):
            score += 0.10
        
        # Location / remote preferences
        pref = getattr(cv, "job_type_preference", None)

        if pref == "remote":
            if "remote" in rec.get("location", "").lower():
                score += 0.10
            else:
                # Penalize non-remote when candidate wants remote
                score *= 0.70
        else:
            # Prefer matching locations
            if any(loc.lower() in rec.get("location", "").lower() for loc in cv_locations):
                score += 0.05
            else:
                # If candidate specified preferred locations and this job doesn't match, apply small penalty
                if cv_locations:
                    score *= 0.85


        # penalize if seniority mismatch, but don't zero out
        if not (rec["seniority"] & allowed_seniority):
            score *= 0.65   # penalty for seniority mismatch

        logger.debug(
            f"Match | Job {rec['id']} | score={score:.4f} | sim={similarities[idx]:.4f} | Job title: '{rec['title']}'"
        )

        job_obj = rec["job"]
        job_obj.match_score = round(score, 3)
        try:
            # try to update only match_score field
            job_obj.save(update_fields=["match_score"])
        except Exception:
            # fallback full save
            job_obj.save()

        scored.append((job_obj, score))

    # sort once after all scores computed
    scored.sort(key=lambda x: x[1], reverse=True)

    # RETURN ONLY JOB OBJECTS
    return [job for job, _ in scored[:top_n]]