from flask import Flask

from .db import get_db_status, init_db


def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    db_status = get_db_status()

    if db_status["connected"]:
        try:
            init_db()
        except Exception as exc:
            db_status = {
                "connected": False,
                "database": db_status["database"],
                "error": f"MongoDB initialization failed: {exc}",
            }
            print(db_status["error"])

    app.config["DB_STATUS"] = db_status

    from .routes.jobs import jobs_bp
    from .routes.pages import pages_bp

    app.register_blueprint(jobs_bp)
    app.register_blueprint(pages_bp)

    return app
