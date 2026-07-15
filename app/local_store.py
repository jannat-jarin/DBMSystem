import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "demo_jobs.json"

DEFAULT_JOBS = [
    {
        "_id": "demo-google-backend",
        "company": "Google",
        "position": "Backend Developer Intern",
        "location": "Remote",
        "platform": "LinkedIn",
        "application_date": "2026-04-28",
        "deadline": "2026-05-09",
        "status": "interview",
        "job_link": "https://careers.google.com",
        "reminder": "Prepare for technical screening on Monday",
        "interview_notes": "Focus on Python, APIs, and database design questions.",
        "created_at": "2026-04-28T10:15:00",
        "updated_at": "2026-04-30T18:20:00",
    },
    {
        "_id": "demo-microsoft-data",
        "company": "Microsoft",
        "position": "Data Analyst",
        "location": "Hybrid",
        "platform": "Company Website",
        "application_date": "2026-04-25",
        "deadline": "2026-05-11",
        "status": "applied",
        "job_link": "https://careers.microsoft.com",
        "reminder": "Check application portal after 5 days",
        "interview_notes": "",
        "created_at": "2026-04-25T14:10:00",
        "updated_at": "2026-04-25T14:10:00",
    },
    {
        "_id": "demo-amazon-cloud",
        "company": "Amazon",
        "position": "Cloud Support Associate",
        "location": "On-site",
        "platform": "Bdjobs",
        "application_date": "2026-04-21",
        "deadline": "2026-05-05",
        "status": "rejected",
        "job_link": "https://amazon.jobs",
        "reminder": "",
        "interview_notes": "Rejected after online assessment. Need more DSA practice.",
        "created_at": "2026-04-21T09:00:00",
        "updated_at": "2026-04-27T16:45:00",
    },
    {
        "_id": "demo-shopify-frontend",
        "company": "Shopify",
        "position": "Junior Frontend Developer",
        "location": "Remote",
        "platform": "Referral",
        "application_date": "2026-04-30",
        "deadline": "2026-05-14",
        "status": "selected",
        "job_link": "https://www.shopify.com/careers",
        "reminder": "Send updated portfolio and transcripts",
        "interview_notes": "Final round cleared. Waiting for offer details.",
        "created_at": "2026-04-30T12:30:00",
        "updated_at": "2026-05-01T11:05:00",
    },
]


def ensure_store():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(DEFAULT_JOBS, indent=2), encoding="utf-8")


def _load_jobs():
    ensure_store()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _save_jobs(jobs):
    DATA_FILE.write_text(json.dumps(jobs, indent=2), encoding="utf-8")


def _matches_search(job, search_query):
    if not search_query:
        return True

    query = search_query.lower()
    haystack = " ".join(
        [
            job.get("company", ""),
            job.get("position", ""),
            job.get("location", ""),
            job.get("platform", ""),
        ]
    ).lower()
    return query in haystack


def _sort_key(job):
    return job.get("application_date", "")


def list_jobs(status_filter=None, search_query=None):
    jobs = _load_jobs()

    filtered_jobs = []
    for job in jobs:
        if job.get("is_deleted") is True:
            continue
        if status_filter and job.get("status") != status_filter:
            continue
        if not _matches_search(job, search_query):
            continue
        filtered_jobs.append(job)

    return sorted(filtered_jobs, key=_sort_key, reverse=True)


def get_job(job_id):
    jobs = _load_jobs()
    for job in jobs:
        if job.get("_id") == job_id and job.get("is_deleted") is not True:
            return job
    return None


def _normalize_for_local(payload):
    normalized = deepcopy(payload)

    for field in ["application_date", "deadline"]:
        if isinstance(normalized.get(field), datetime):
            normalized[field] = normalized[field].strftime("%Y-%m-%d")

    for field in ["created_at", "updated_at"]:
        if isinstance(normalized.get(field), datetime):
            normalized[field] = normalized[field].isoformat()

    return normalized


def create_job(payload):
    jobs = _load_jobs()
    job = _normalize_for_local(payload)
    job["_id"] = uuid4().hex
    job["is_deleted"] = False
    job["deleted_at"] = None
    jobs.append(job)
    _save_jobs(jobs)
    return job


def update_job(job_id, updates):
    jobs = _load_jobs()
    normalized_updates = _normalize_for_local(updates)

    for index, job in enumerate(jobs):
        if job.get("_id") == job_id and job.get("is_deleted") is not True:
            jobs[index] = {**job, **normalized_updates}
            _save_jobs(jobs)
            return jobs[index]

    return None


def delete_job(job_id):
    jobs = _load_jobs()
    deleted = False

    for index, job in enumerate(jobs):
        if job.get("_id") == job_id and job.get("is_deleted") is not True:
            jobs[index]["is_deleted"] = True
            jobs[index]["deleted_at"] = datetime.utcnow().isoformat()
            jobs[index]["updated_at"] = datetime.utcnow().isoformat()
            deleted = True
            break

    if deleted:
        _save_jobs(jobs)

    return deleted


def get_stats():
    jobs = _load_jobs()
    stats = {
        "total": len(jobs),
        "applied": 0,
        "interview": 0,
        "selected": 0,
        "rejected": 0,
        "upcoming_deadlines": 0,
    }

    today = datetime.utcnow().strftime("%Y-%m-%d")

    for job in jobs:
        if job.get("is_deleted") is True:
            continue
        status = job.get("status")
        if status in stats:
            stats[status] += 1

        deadline = job.get("deadline")
        if deadline and deadline >= today:
            stats["upcoming_deadlines"] += 1

    stats["total"] = sum(stats[key] for key in ["applied", "interview", "selected", "rejected"])
    return stats
