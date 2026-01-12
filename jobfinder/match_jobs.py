from sklearn.feature_extraction.text import TfidfVectorizer # for TF-IDF
from sklearn.metrics.pairwise import cosine_similarity # for similarity calculation
from jobfinder.models import Job
from users.models import CV
import pandas as pd
import re # for text cleaning

from jobfinder.logging_config import setup_logger
logger = setup_logger("matcher", "matcher.log")


# text normalization function
def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    # keep letters, numbers, +, #, -, . and spaces (preserve common tech names)
    text = re.sub(r"[^a-z0-9+#\-\.\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text



# main matching function
def match_jobs_to_cv(cv_id, top_n=5):
    try:
        cv = CV.objects.get(id=cv_id)
    except CV.DoesNotExist:
        logger.error(f"CV with id {cv_id} does not exist.")
        return []

    def split_set(text):
        if not text:
            return set()
        tokens = re.findall(r"[a-z0-9+#\-\.]+", normalize_text(text))
        return set(t for t in tokens if t)

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

    SENIORITY_KEYWORDS = {
        "intern": {"intern", "internship", "trainee"},
        "junior": {"junior", "jr", "associate", "entry", "graduate"},
        "mid": {"mid", "intermediate", "regular"},
        "senior": {"senior", "sr", "lead", "principal", "staff"},
    }

    def detect_job_seniority(text):
        found = set()
        for level, keys in SENIORITY_KEYWORDS.items():
            for k in keys:
                if re.search(rf"\b{re.escape(k)}\b", text):
                    found.add(level)
        return found

    # detect required years in job text, return minimal integer if found
    def detect_required_experience(text):
        if not text:
            return None
        # common patterns: "5 years", "5+ years", "6+ years of experience", "minimum 4 years"
        m = re.search(r"(?:(?:minimum|min|min\.)\s*)?(\d{1,2})\s*\+?\s*(?:\+|\s)?\s*(?:years|yrs)\b", text)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
        return None

    # Combine CV fields into a single text
    cv_text = " ".join([
        normalize_text(cv.skills),
        normalize_text(cv.technologies),
        normalize_text(cv.preferred_roles),
        normalize_text(cv.experience),
        normalize_text(cv.education),
    ])

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
        title = normalize_text(job.title or job.position or "")
        desc = normalize_text(job.description or "")
        tags = ""
        if isinstance(job.attributes, list):
            tag_parts = []
            for t in job.attributes:
                if isinstance(t, dict):
                    tag_parts.append(t.get("slug") or t.get("name") or "")
                else:
                    tag_parts.append(str(t))
            tags = " ".join(normalize_text(p) for p in tag_parts if p)
        combined = f"{title} {tags} {desc}"
        job_seniority = detect_job_seniority(f"{title} {tags}")
        required_exp = detect_required_experience(combined)
        job_tags = (split_set(title) | split_set(tags))

        records.append({
            "id": job.id,
            "job": job,
            "text": combined,
            "title": title,
            "seniority": job_seniority,
            "required_experience": required_exp,
            "location": normalize_text(job.location or ""),
            "salary_min": job.salary,
            "salary_max": job.salary,
            "job_tags": job_tags,
        })

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_df=0.9,
        min_df=1,
    )

    job_vectors = vectorizer.fit_transform([r["text"] for r in records])
    cv_vector = vectorizer.transform([cv_text])
    similarities = cosine_similarity(cv_vector, job_vectors).flatten()

    results = []

    # simpler scoring: baseline + additive boosts, multiplicative penalties
    for idx, rec in enumerate(records):
        sim = float(similarities[idx]) if idx < len(similarities) else 0.0

        # baseline to bias results toward ~50% on average
        score = 0.35

        # semantic similarity (adds up to +0.25)
        score += sim * 0.25

        # skill matches (adds up to +0.20)
        exact_skill_matches = len(cv_skills & rec["job_tags"])
        if cv_skills:
            frac = exact_skill_matches / max(1, len(cv_skills))
            score += 0.20 * frac

        # tech matches (adds up to +0.15)
        exact_tech_matches = len(cv_tech & rec["job_tags"])
        if cv_tech:
            frac_tech = exact_tech_matches / max(1, len(cv_tech))
            score += 0.15 * frac_tech

        # seniority: small boost or multiplicative penalty
        seniority_match = False
        if rec["seniority"]:
            seniority_match = bool(rec["seniority"] & allowed_seniority)
            if seniority_match:
                score += 0.05
            else:
                score *= 0.8

        # required experience: small boost or penalty
        req_exp = rec.get("required_experience")
        if req_exp is not None and cv.experience_years is not None:
            if cv.experience_years >= req_exp:
                score += 0.05
            else:
                score *= 0.8

        # role/title match
        if cv_roles:
            role_match = any(re.search(rf"\b{re.escape(role)}\b", rec["title"]) for role in cv_roles if role)
            if role_match:
                score += 0.03

        # location / remote preference
        pref = getattr(cv, "job_type_preference", None)
        loc_field = rec.get("location", "")
        if pref == "remote":
            if "remote" in loc_field:
                score += 0.02
            else:
                score *= 0.95
        elif cv_locations:
            loc_match = any(loc.lower() in loc_field for loc in cv_locations)
            if loc_match:
                score += 0.03
            else:
                score *= 0.95

        # clamp and convert to percent (0..100)
        score = max(0.0, min(1.0, score))
        percent_score = round(score * 100, 2)

        logger.debug(
            f"Match | Job {rec['id']} | percent={percent_score:.2f}% | raw_score={score:.4f} "
            f"| sim={sim:.4f} skills={exact_skill_matches} techs={exact_tech_matches}"
        )

        results.append({
            "job": rec["job"],
            "score": percent_score,
            "seniority_match": seniority_match,
            "experience_bucket": list(allowed_seniority),
        })

    # sort and persist only top_n match_score to reduce DB writes
    results.sort(key=lambda r: r["score"], reverse=True)
    top_results = results[:top_n]

    for r in top_results:
        job_obj = r["job"]
        bounded = max(0.0, min(100.0, float(r["score"])))
        job_obj.match_score = bounded
        try:
            job_obj.save(update_fields=["match_score"])
        except Exception:
            try:
                job_obj.save()
            except Exception:
                logger.exception(f"Failed to save match_score for job {job_obj.id}")

    return top_results