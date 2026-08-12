import json
from pathlib import Path

import pytest
from app.server import app
from app.schemas import QwenOutput


def test_qwen_output_normalizes_yue_compatible_variants():
    output = QwenOutput(
        title="Cell Song",
        subject="Biology",
        topic="Cells",
        difficulty="Grade 8",
        genre_tags=["uplifting pop", "educational anthem", "energetic"],
        key_facts=["Cells have membranes."],
        learning_objectives=["Identify cell membranes."],
        lyrics="[verse 1]\nCells have membranes.\n\n[chorus]\nCells are life.",
        music_prompt="Energetic educational pop song.",
    )
    assert output.genre_tags == "uplifting pop educational anthem energetic"


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
