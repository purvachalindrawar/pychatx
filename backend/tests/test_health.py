import os

# Force tests to use a local SQLite DB, not Neon
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.db import Base, engine  # noqa: E402

# Ensure tables exist for SQLite tests
Base.metadata.create_all(bind=engine)

def test_health():
    client = TestClient(app)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
