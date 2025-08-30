import os

# Force tests to use a local SQLite DB, not Neon
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.db import Base, engine  # noqa: E402

# Ensure tables exist for SQLite tests
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_create_and_list_users():
    # create
    res = client.post("/api/v1/users", json={"email": "bob@example.com", "display_name": "Bob"})
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "bob@example.com"
    assert data["display_name"] == "Bob"

    # list
    res = client.get("/api/v1/users")
    assert res.status_code == 200
    users = res.json()
    assert any(u["email"] == "bob@example.com" for u in users)
