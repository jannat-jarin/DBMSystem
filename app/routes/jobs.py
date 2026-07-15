from datetime import datetime

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request

from ..db import jobs_collection
from ..local_store import (
    create_job as create_local_job,
    delete_job as delete_local_job,
    get_job as get_local_job,
    get_stats as get_local_stats,
    list_jobs as list_local_jobs,
    update_job as update_local_job,
)

jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")

STATUS_OPTIONS = ["applied", "interview", "rejected", "selected"]
DATE_FIELDS = ["application_date", "deadline"]


def is_database_connected():
    status = current_app.config.get("DB_STATUS", {})
    return status.get("connected", False)


def get_storage_mode():
    return "mongodb" if is_database_connected() else "local_demo"


def normalize_text(value):
    return str(value or "").strip()


def build_mongo_id_query(job_id):
    if ObjectId.is_valid(job_id):
        return {"$or": [{"_id": ObjectId(job_id)}, {"_id": job_id}]}
    return {"_id": job_id}


def active_job_query(extra_query=None):
    query = {"is_deleted": {"$ne": True}}
    if extra_query:
        query.update(extra_query)
    return query


def parse_date(value, field_name):
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_name} must be YYYY-MM-DD")


def serialize_job(job):
    serialized = dict(job)
    serialized["_id"] = str(serialized["_id"])

    for field in DATE_FIELDS:
        if isinstance(serialized.get(field), datetime):
            serialized[field] = serialized[field].strftime("%Y-%m-%d")

    for field in ["created_at", "updated_at"]:
        if isinstance(serialized.get(field), datetime):
            serialized[field] = serialized[field].isoformat()

    return serialized


def build_job_payload(data, partial=False):
    payload = {}

    required_fields = ["company", "position", "application_date"]
    if not partial:
        for field in required_fields:
            if not normalize_text(data.get(field)):
                raise ValueError(f"'{field}' is required")

    text_fields = [
        "company",
        "position",
        "location",
        "platform",
        "job_link",
        "reminder",
        "interview_notes",
    ]

    for field in text_fields:
        if field in data:
            payload[field] = normalize_text(data.get(field))

    if "status" in data:
        status_value = normalize_text(data.get("status")).lower()
        if status_value not in STATUS_OPTIONS:
            raise ValueError(f"status must be one of {STATUS_OPTIONS}")
        payload["status"] = status_value
    elif not partial:
        payload["status"] = "applied"

    for field in DATE_FIELDS:
        if field in data:
            payload[field] = parse_date(data.get(field), field)

    if not partial:
        payload.setdefault("location", "")
        payload.setdefault("platform", "")
        payload.setdefault("job_link", "")
        payload.setdefault("reminder", "")
        payload.setdefault("interview_notes", "")

    return payload


@jobs_bp.route("/health", methods=["GET"])
def health_check():
    status = dict(current_app.config.get("DB_STATUS", {}))
    status["storage_mode"] = get_storage_mode()

    if status["storage_mode"] == "local_demo":
        status["message"] = "Running with local demo data because MongoDB is unavailable."

    http_status = 200 if status.get("connected") else 503
    return jsonify(status), http_status


@jobs_bp.route("/", methods=["GET"])
def get_jobs():
    status_filter = normalize_text(request.args.get("status")).lower()
    search_query = normalize_text(request.args.get("q"))

    if is_database_connected():
        query = active_job_query()
        if status_filter and status_filter in STATUS_OPTIONS:
            query["status"] = status_filter

        if search_query:
            query["$or"] = [
                {"company": {"$regex": search_query, "$options": "i"}},
                {"position": {"$regex": search_query, "$options": "i"}},
                {"location": {"$regex": search_query, "$options": "i"}},
                {"platform": {"$regex": search_query, "$options": "i"}},
            ]

        jobs = list(jobs_collection.find(query).sort("application_date", -1))
        return jsonify([serialize_job(job) for job in jobs])

    jobs = list_local_jobs(status_filter=status_filter or None, search_query=search_query or None)
    return jsonify([serialize_job(job) for job in jobs])


@jobs_bp.route("/<job_id>", methods=["GET"])
def get_job(job_id):
    if is_database_connected():
        job = jobs_collection.find_one(
            {"$and": [active_job_query(), build_mongo_id_query(job_id)]}
        )

        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify(serialize_job(job))

    job = get_local_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(serialize_job(job))


@jobs_bp.route("/", methods=["POST"])
def create_job():
    data = request.get_json(silent=True) or {}

    try:
        job = build_job_payload(data, partial=False)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    job["created_at"] = datetime.utcnow()
    job["updated_at"] = datetime.utcnow()
    job["is_deleted"] = False
    job["deleted_at"] = None

    if is_database_connected():
        result = jobs_collection.insert_one(job)
        created_job = jobs_collection.find_one({"_id": result.inserted_id})
        return jsonify(serialize_job(created_job)), 201

    created_job = create_local_job(job)
    return jsonify(serialize_job(created_job)), 201


@jobs_bp.route("/<job_id>", methods=["PUT"])
def update_job(job_id):
    data = request.get_json(silent=True) or {}

    try:
        updates = build_job_payload(data, partial=True)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not updates:
        return jsonify({"error": "No valid fields provided for update"}), 400

    updates["updated_at"] = datetime.utcnow()

    if is_database_connected():
        result = jobs_collection.update_one(
            {"$and": [active_job_query(), build_mongo_id_query(job_id)]},
            {"$set": updates},
        )
        if result.matched_count == 0:
            return jsonify({"error": "Job not found"}), 404

        updated_job = jobs_collection.find_one(
            {"$and": [active_job_query(), build_mongo_id_query(job_id)]}
        )
        return jsonify(serialize_job(updated_job))

    updated_job = update_local_job(job_id, updates)
    if not updated_job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(serialize_job(updated_job))


@jobs_bp.route("/<job_id>", methods=["DELETE"])
def delete_job(job_id):
    if is_database_connected():
        result = jobs_collection.update_one(
            {"$and": [active_job_query(), build_mongo_id_query(job_id)]},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        if result.matched_count == 0:
            return jsonify({"error": "Job not found"}), 404

        return jsonify({"message": "Job hidden successfully"})

    deleted = delete_local_job(job_id)
    if not deleted:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"message": "Job deleted successfully"})


@jobs_bp.route("/stats/summary", methods=["GET"])
def get_stats():
    if is_database_connected():
        pipeline = [
            {"$match": active_job_query()},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        result = list(jobs_collection.aggregate(pipeline))
        stats = {item["_id"]: item["count"] for item in result}

        total = sum(stats.values())
        today = datetime.utcnow()
        upcoming_deadlines = jobs_collection.count_documents(
            active_job_query({"deadline": {"$gte": datetime(today.year, today.month, today.day)}})
        )

        return jsonify(
            {
                "total": total,
                "applied": stats.get("applied", 0),
                "interview": stats.get("interview", 0),
                "selected": stats.get("selected", 0),
                "rejected": stats.get("rejected", 0),
                "upcoming_deadlines": upcoming_deadlines,
                "storage_mode": "mongodb",
            }
        )

    stats = get_local_stats()
    stats["storage_mode"] = "local_demo"
    return jsonify(stats)
