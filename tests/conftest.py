import pytest

import database.db as db
from app import app as flask_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()

    flask_app.config["TESTING"] = True
    yield flask_app
