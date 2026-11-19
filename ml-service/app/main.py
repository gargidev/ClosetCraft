from __future__ import annotations

import base64
import binascii
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from app.schemas.models import (
    OutfitRecommendationRequest, RecommendationResponse,
    AccessoryRequest, AccessoryResponse, ClassificationRequest,
    ClassificationResponse, FeedbackRequest,
)
from app.recommendation.engine import OutfitRecommendationEngine
from app.models.clip_service import CLIPEmbeddingService
from app.models.garment_classifier import GarmentImageClassifier

app = FastAPI(
    title="Closet Craft ML Recommendation Service",
    description="Image-based garment classification and outfit recommendation",
    version="2.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = OutfitRecommendationEngine()
clip = CLIPEmbeddingService()
classifier = GarmentImageClassifier(clip)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "closet-craft-ml",
        "clip_model": clip.model_name,
        "clip_loaded": clip.is_loaded,
        "image_classifier_available": classifier.is_available,
        "supervised_head_loaded": classifier.head is not None,
        "device": clip.device,
        "ranking_weights": engine.weights,
    }


@app.post("/embeddings")
def compute_embedding(data: dict):
    text = data.get("text", "")
    vector = clip.get_embedding(text)
    return {"model": clip.model_name, "dimensions": len(vector), "embedding": vector, "clip_loaded": clip.is_loaded}


def _decode_image(value: str) -> Image.Image:
    if not value:
        raise HTTPException(status_code=400, detail="Provide image_base64_or_url as a base64 data URL or raw base64 string.")
    if value.startswith("data:"):
        try:
            header, value = value.split(",", 1)
            if ";base64" not in header:
                raise ValueError("Only base64 data URLs are supported")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    # Remote URLs are intentionally not fetched here: accepting arbitrary URLs
    # can create SSRF vulnerabilities. The API accepts base64 image content.
    try:
        raw = base64.b64decode(value, validate=True)
        if len(raw) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Image exceeds the 10 MB limit.")
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        if image.width < 32 or image.height < 32:
            raise HTTPException(status_code=400, detail="Image is too small to classify.")
        return image
    except (binascii.Error, UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid image. Upload a valid JPG, PNG, or WEBP photo.")


@app.post("/classify-garment")
def classify_garment(req: ClassificationRequest):
    if not classifier.is_available:
        raise HTTPException(
            status_code=503,
            detail="Image classification model is unavailable. Install ML dependencies and allow the CLIP checkpoint to load.",
        )
    image = _decode_image(req.image_base64_or_url)
    try:
        return classifier.classify(image)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image classification failed: {type(exc).__name__}")


@app.post("/recommend-outfits", response_model=RecommendationResponse)
def recommend_outfits(req: OutfitRecommendationRequest):
    return engine.generate_recommendations(req)


@app.post("/recommend-accessories", response_model=AccessoryResponse)
def recommend_accessories(req: AccessoryRequest):
    owned = [
        a for a in req.available_accessories
        if a.category.lower() in ["accessories", "bags", "jewellery", "sunglasses"]
        and a.status.replace(" ", "").replace("_", "").lower() not in {"inlaundry", "washing", "drying", "damaged", "worn", "unavailable"}
    ]
    notes = [
        f"Selected matching pieces to harmonize with {', '.join(req.outfit_colors[:2]) if req.outfit_colors else 'your look'}.",
        "Choose one focal accessory to keep the outfit balanced.",
    ]
    return AccessoryResponse(status="success", owned_accessories=owned[:3], suggested_styling_notes=notes)


@app.post("/feedback")
def record_feedback(req: FeedbackRequest):
    return {"status": "recorded", "outfit_id": req.outfit_id, "reward": 1.0 if req.is_vibe else 0.0}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
