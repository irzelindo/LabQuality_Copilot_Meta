import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from app.config import settings
from app.database import engine, session_factory
from app.demo import seed_demo

PASSWORD = "Local-demo-test-2026!"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LQ_DATABASE_URL", "sqlite:///" + str(tmp_path / "test.db"))
    monkeypatch.setenv("LQ_STORAGE_DIR", str(tmp_path / "files"))
    monkeypatch.setenv("LQ_MODEL_API_KEY", "")
    monkeypatch.setenv("LQ_SMTP_HOST", "")
    settings.cache_clear()
    engine.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    with session_factory()() as db:
        seed_demo(db, PASSWORD, scenario="legacy")
        db.commit()
    from app.main import app
    with TestClient(app, headers={"X-LabQuality-Client": "web"}) as c:
        yield c
    engine().dispose()
    engine.cache_clear()
    settings.cache_clear()


def login(client, email="admin@labquality.local"):
    result = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert result.status_code == 200, result.text
    return result.json()
