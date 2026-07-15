"""
Run this once to add sample job data:
    python seed.py
"""

from datetime import datetime

from app.db import client, jobs_collection

jobs_collection.delete_many({})

sample_jobs = [
    {
        "company": "Google",
        "position": "Software Engineer",
        "location": "Remote",
        "platform": "LinkedIn",
        "application_date": datetime(2026, 4, 10),
        "deadline": datetime(2026, 5, 18),
        "status": "interview",
        "job_link": "https://careers.google.com/jobs/results/123",
        "reminder": "Prepare for the second round next Tuesday",
        "interview_notes": "Round 1 completed. Review system design and REST APIs.",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "company": "Meta",
        "position": "Backend Developer",
        "location": "Dhaka",
        "platform": "Company website",
        "application_date": datetime(2026, 4, 15),
        "deadline": datetime(2026, 5, 20),
        "status": "applied",
        "job_link": "https://careers.meta.com/jobs/results/456",
        "reminder": "Check recruiter email after 5 days",
        "interview_notes": "",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "company": "Amazon",
        "position": "Cloud Engineer",
        "location": "Hybrid",
        "platform": "Bdjobs",
        "application_date": datetime(2026, 4, 5),
        "deadline": datetime(2026, 5, 8),
        "status": "rejected",
        "job_link": "https://amazon.jobs/en/jobs/789",
        "reminder": "",
        "interview_notes": "Rejected after OA. Practice more DSA before reapplying.",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
    {
        "company": "Grameenphone",
        "position": "Python Developer",
        "location": "Dhaka",
        "platform": "Referral",
        "application_date": datetime(2026, 4, 20),
        "deadline": datetime(2026, 5, 25),
        "status": "selected",
        "job_link": "",
        "reminder": "Send joining documents this week",
        "interview_notes": "Selected. Salary discussion done and onboarding pending.",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    },
]

jobs_collection.insert_many(sample_jobs)
print(f"{len(sample_jobs)} sample jobs inserted.")
client.close()
