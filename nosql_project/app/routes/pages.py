from datetime import date, datetime

from flask import Blueprint, current_app, render_template

from ..db import jobs_collection
from ..local_store import get_stats as get_local_stats
from .jobs import STATUS_OPTIONS

pages_bp = Blueprint("pages", __name__)


def get_initial_stats(db_status):
    if not db_status.get("connected", False):
        stats = get_local_stats()
        stats["storage_mode"] = "local_demo"
        return stats

    pipeline = [
        {"$match": {"is_deleted": {"$ne": True}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    result = list(jobs_collection.aggregate(pipeline))
    stats = {item["_id"]: item["count"] for item in result}

    today = datetime.utcnow()
    upcoming_deadlines = jobs_collection.count_documents(
        {
            "is_deleted": {"$ne": True},
            "deadline": {"$gte": datetime(today.year, today.month, today.day)},
        }
    )

    return {
        "total": sum(stats.values()),
        "applied": stats.get("applied", 0),
        "interview": stats.get("interview", 0),
        "selected": stats.get("selected", 0),
        "rejected": stats.get("rejected", 0),
        "upcoming_deadlines": upcoming_deadlines,
        "storage_mode": "mongodb",
    }


@pages_bp.route("/")
def index():
    db_status = current_app.config.get("DB_STATUS", {})
    initial_stats = get_initial_stats(db_status)
    return render_template(
        "index.html",
        status_options=STATUS_OPTIONS,
        db_status=db_status,
        initial_stats=initial_stats,
        asset_version=datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        today=date.today().isoformat(),
    )
