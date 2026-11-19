import os
import sys
import tempfile
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Ensure backend directory is on sys.path when imported or run directly
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database.db import configure_database, db
from routes.api_routes import api_bp, seed_initial_data


def _resolve_writable_upload_dir(default_dir):
    try:
        os.makedirs(default_dir, exist_ok=True)
        probe = os.path.join(default_dir, ".write_test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
        return default_dir
    except Exception:
        fallback = os.path.join(tempfile.gettempdir(), "animalcare_uploads")
        os.makedirs(fallback, exist_ok=True)
        return fallback


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    default_uploads_dir = os.path.join(BACKEND_DIR, "uploads")
    app.config["UPLOAD_FOLDER"] = _resolve_writable_upload_dir(default_uploads_dir)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB limit

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
            "message": "Flask backend and SQLite database are active.",
            "endpoints": [
                "/api/health",
                "/api/animals",
                "/api/symptoms",
                "/api/diseases",
                "/api/upload",
                "/api/history",
                "/api/predictions"
            ]
        })

    @app.route("/uploads/<path:filename>", methods=["GET"])
    def serve_uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
