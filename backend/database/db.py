import os
import sqlite3
import tempfile
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _is_sqlite_path_writable(db_path):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS _write_check (id INTEGER)")
        conn.execute("INSERT INTO _write_check (id) VALUES (1)")
        conn.execute("DELETE FROM _write_check")
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def configure_database(app, backend_dir):
    db_dir = os.path.join(backend_dir, "database")
    os.makedirs(db_dir, exist_ok=True)
    default_db_path = os.path.join(db_dir, "animalcare.db")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        if _is_sqlite_path_writable(default_db_path):
            chosen_path = default_db_path
        else:
            chosen_path = os.path.join(tempfile.gettempdir(), "animalcare.db")
        database_url = "sqlite:///" + chosen_path.replace("\\", "/")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
