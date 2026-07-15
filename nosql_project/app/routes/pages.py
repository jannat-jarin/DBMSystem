from datetime import date

from flask import Blueprint, current_app, render_template

from .jobs import STATUS_OPTIONS

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    db_status = current_app.config.get("DB_STATUS", {})
    return render_template(
        "index.html",
        status_options=STATUS_OPTIONS,
        db_status=db_status,
        today=date.today().isoformat(),
    )
