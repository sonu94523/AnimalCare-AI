import logging
import os
import tempfile
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)
db = SQLAlchemy()


def _is_dir_and_file_writable(db_path: str) -> bool:
    """Check writability using OS permissions/probe file without mutating the SQLite schema."""
    db_dir = os.path.dirname(db_path)
    try:
        os.makedirs(db_dir, exist_ok=True)
        if os.path.exists(db_path):
            with open(db_path, "r+b"):
                return True
        probe_path = os.path.join(db_dir, ".db_write_probe")
        with open(probe_path, "wb") as f:
            f.write(b"ok")
        os.remove(probe_path)
        return True
    except OSError as exc:
        logger.warning("Database path %s is not writable (%s); falling back to temp dir.", db_path, exc)
        return False


def configure_database(app, backend_dir: str) -> None:
    """Configure SQLAlchemy URI from app.config, DATABASE_URL, or local SQLite file."""
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            default_db_path = os.path.join(backend_dir, "database", "animalcare.db")
            if _is_dir_and_file_writable(default_db_path):
                chosen_path = default_db_path
            else:
                chosen_path = os.path.join(tempfile.gettempdir(), "animalcare.db")
            database_url = "sqlite:///" + chosen_path.replace("\\", "/")
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db.init_app(app)
