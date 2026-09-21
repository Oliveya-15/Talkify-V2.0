import time

import pytest
from fastapi.testclient import TestClient

import app.main as m
from app.database import Base, engine


@pytest.fixture()
def client():
    # Drop and recreate all tables before each test so tests never leak
    # state into each other (this uses the same SQLite file configured
    # by DATABASE_URL — fine for a student project; a CI setup would
    # typically point DATABASE_URL at a dedicated throwaway test DB).
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(m.app) as c:
        yield c


def _register(client, email="a@example.com"):
    r = client.post("/api/auth/register", json={"name": "A", "email": email, "password": "password123"})
    assert r.status_code == 201
    return r.json()["access_token"]


def test_register_and_login(client):
    token = _register(client)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@example.com"


def test_unauthorized_access_is_rejected(client):
    r = client.get("/api/documents")
    assert r.status_code == 401


def test_invalid_token_is_rejected(client):
    r = client.get("/api/documents", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_upload_rejects_unsupported_file_type(client):
    token = _register(client)
    r = client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("malware.exe", b"fake binary content", "application/octet-stream")},
    )
    assert r.status_code == 422


def test_upload_rejects_empty_file(client):
    token = _register(client)
    r = client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert r.status_code == 422


def test_txt_upload_processes_successfully(client):
    """
    End-to-end: upload -> extract -> chunk -> embed -> index -> completed.
    Processing now runs in a FastAPI BackgroundTask (see api/routes/documents.py)
    so the upload response returns immediately with status "uploaded" — this
    test polls the document until it reaches a terminal state, the same way
    the frontend's Documents.jsx does.

    This also needs the sentence-transformers model, downloaded from
    huggingface.co on first use. If that network call isn't available (e.g.
    an offline sandbox), we skip rather than fail — the important thing is
    that IF embeddings can run, the whole pipeline produces a "completed"
    document with real chunks.
    """
    token = _register(client)
    headers = {"Authorization": f"Bearer {token}"}
    content = b"Machine learning is a subset of artificial intelligence. " * 20
    r = client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("ml_notes.txt", content, "text/plain")},
    )
    assert r.status_code == 201
    doc_id = r.json()["id"]

    body = None
    for _ in range(30):
        body = client.get(f"/api/documents/{doc_id}", headers=headers).json()
        if body["processing_status"] in ("completed", "failed"):
            break
        time.sleep(0.5)

    if body["processing_status"] == "failed" and "connect" in (body.get("processing_error") or "").lower():
        pytest.skip("Embedding model unavailable offline — this environment has no internet access.")
    assert body["processing_status"] == "completed"
    assert body["file_name"] == "ml_notes.txt"


def test_users_cannot_see_each_others_documents(client):
    token_a = _register(client, email="usera@example.com")
    token_b = _register(client, email="userb@example.com")

    upload = client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("private.txt", b"User A's private notes about their research.", "text/plain")},
    )
    doc_id = upload.json()["id"]

    # user B should not be able to fetch user A's document
    r = client.get(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 404

    # user B's own document list should be empty
    r = client.get("/api/documents", headers={"Authorization": f"Bearer {token_b}"})
    assert r.json() == []


def test_duplicate_registration_rejected(client):
    _register(client, email="dup@example.com")
    r = client.post("/api/auth/register", json={"name": "Dup", "email": "dup@example.com", "password": "password123"})
    assert r.status_code == 400
