import logging
import os
import tempfile
from typing import Any, Dict, Optional

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from backend.database.db import configure_database, db
from backend.routes.api_routes import api_bp, seed_initial_data
from ml.constants import DEFAULT_SAVED_MODELS_DIR
from ml.preprocessing import DEFAULT_DATASET_DIR

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)


def _resolve_writable_upload_dir(default_dir: str) -> str:
    try:
        os.makedirs(default_dir, exist_ok=True)
        probe = os.path.join(default_dir, ".write_test")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return default_dir
    except OSError as exc:
        fallback = os.path.join(tempfile.gettempdir(), "animalcare_uploads")
        logger.warning("Upload folder %s not writable (%s); using %s.", default_dir, exc, fallback)
        os.makedirs(fallback, exist_ok=True)
        return fallback


def _parse_cors_origins(raw: Optional[str]):
    default = ["http://localhost:5173", "http://127.0.0.1:5173"]
    if not raw:
        return default
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or default


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """Application factory. Pass `config` overrides for isolated testing."""
    app = Flask(__name__)

    if config:
        app.config.update(config)

    cors_origins = app.config.get("CORS_ORIGINS") or _parse_cors_origins(os.getenv("CORS_ORIGINS"))
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    if not app.config.get("UPLOAD_FOLDER"):
        app.config["UPLOAD_FOLDER"] = _resolve_writable_upload_dir(os.path.join(BACKEND_DIR, "uploads"))
    else:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    if app.config.get("MAX_CONTENT_LENGTH") is None:
        app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB limit
    app.config.setdefault("MODELS_DIR", os.getenv("MODELS_DIR") or DEFAULT_SAVED_MODELS_DIR)
    app.config.setdefault("DATASET_DIR", os.getenv("DATASET_DIR") or DEFAULT_DATASET_DIR)
    app.config.setdefault("ADMIN_TOKEN", os.getenv("ADMIN_TOKEN", ""))

    configure_database(app, BACKEND_DIR)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        seed_initial_data()

    @app.errorhandler(413)
    def request_entity_too_large(_error):
        return jsonify({"error": "Image file size exceeds the 5 MB maximum limit."}), 413

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "project": "AnimalCare AI - Animal Disease Detection System",
            "status": "running",
            "endpoints": [
                "/api/health",
                "/api/animals",
                "/api/symptoms",
                "/api/symptoms/submit",
                "/api/diseases",
                "/api/upload",
                "/api/predict/image",
                "/api/predict/combined",
                "/api/model/info",
                "/api/history",
            ],
        })

    @app.route("/uploads/<path:filename>", methods=["GET"])
    def serve_uploaded_file(filename):
        response = send_from_directory(app.config["UPLOAD_FOLDER"], filename)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    application = create_app()
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG") == "1"
    logger.info("Starting AnimalCare AI backend on http://%s:%d (debug=%s)", host, port, debug)
    application.run(host=host, port=port, debug=debug)
