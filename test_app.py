import json
from pathlib import Path

import pytest
from app.server import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["service"] == "ORPHEUS"


def test_generate_missing_text():
    client = app.test_client()
    response = client.post(
        "/api/generate",
        data=json.dumps({"text": ""}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "study material" in data["error"].lower()


def test_upload_missing_file():
    client = app.test_client()
    response = client.post("/api/upload", data={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_upload_unsupported_file(tmp_path: Path):
    client = app.test_client()
    sample = tmp_path / "document.exe"
    sample.write_text("not supported")
    with open(sample, "rb") as handle:
        response = client.post(
            "/api/upload",
            data={"file": (handle, "document.exe")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
