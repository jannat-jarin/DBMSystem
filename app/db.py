import os

from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "job_tracker_db")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DATABASE_NAME]
jobs_collection = db["jobs"]


def init_db():
    client.admin.command("ping")

    jobs_collection.create_index([("company", ASCENDING)])
    jobs_collection.create_index([("status", ASCENDING)])
    jobs_collection.create_index([("application_date", DESCENDING)])
    jobs_collection.create_index([("deadline", ASCENDING)])
    jobs_collection.create_index(
        [
            ("company", "text"),
            ("position", "text"),
            ("location", "text"),
            ("platform", "text"),
        ]
    )

    print("MongoDB connected and indexes created.")


def get_db_status():
    try:
        client.admin.command("ping")
        return {"connected": True, "database": DATABASE_NAME}
    except Exception as exc:
        return {"connected": False, "database": DATABASE_NAME, "error": str(exc)}
