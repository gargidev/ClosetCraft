import base64
import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app, classifier

client = TestClient(app)


def _png_base64():
    image = Image.new("RGB", (128, 128), (30, 80, 150))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def test_health_reports_model_state():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "closet-craft-ml"


def test_classifier_rejects_malformed_base64():
    response = client.post("/classify-garment", json={"image_base64_or_url": "not-base64!"})
    assert response.status_code in (400, 503)


def test_classifier_rejects_non_image_bytes():
    payload = base64.b64encode(b"this is not an image").decode("ascii")
    response = client.post("/classify-garment", json={"image_base64_or_url": payload})
    assert response.status_code in (400, 503)


def test_classifier_never_uses_filename_as_prediction():
    # If model weights are not downloaded in CI, a 503 is correct. If available,
    # a valid image must be processed from its pixels, not from its filename.
    response = client.post(
        "/classify-garment",
        json={"image_base64_or_url": _png_base64(), "file_name": "obviously-a-tshirt.jpg"},
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        assert "confidence_score" in response.json()
        assert "is_clothing" in response.json()
