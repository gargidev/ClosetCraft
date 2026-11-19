"""Image-based garment classification using CLIP embeddings.

Uses zero-shot CLIP classification until a supervised head is trained and saved.
A trained head is loaded automatically from this module's directory when present.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image

LABELS = [
    ("t_shirt", "a photograph of a t-shirt", "tops"),
    ("shirt", "a photograph of a shirt", "tops"),
    ("blouse", "a photograph of a blouse", "tops"),
    ("tank_top", "a photograph of a tank top", "tops"),
    ("hoodie", "a photograph of a hoodie", "tops"),
    ("sweater", "a photograph of a sweater", "tops"),
    ("kurti", "a photograph of a kurti", "tops"),
    ("jeans", "a photograph of jeans", "bottoms"),
    ("trousers", "a photograph of trousers", "bottoms"),
    ("shorts", "a photograph of shorts", "bottoms"),
    ("skirt", "a photograph of a skirt", "bottoms"),
    ("leggings", "a photograph of leggings", "bottoms"),
    ("dress", "a photograph of a dress", "dresses"),
    ("gown", "a photograph of a gown", "dresses"),
    ("jumpsuit", "a photograph of a jumpsuit", "dresses"),
    ("jacket", "a photograph of a jacket", "outerwear"),
    ("coat", "a photograph of a coat", "outerwear"),
    ("blazer", "a photograph of a blazer", "outerwear"),
    ("sneakers", "a photograph of sneakers", "shoes"),
    ("heels", "a photograph of high heel shoes", "shoes"),
    ("boots", "a photograph of boots", "shoes"),
    ("sandals", "a photograph of sandals", "shoes"),
    ("handbag", "a photograph of a handbag", "bags"),
    ("backpack", "a photograph of a backpack", "bags"),
    ("scarf", "a photograph of a scarf", "accessories"),
    ("belt", "a photograph of a belt", "accessories"),
    ("sunglasses", "a photograph of sunglasses", "accessories"),
    ("jewellery", "a photograph of jewellery", "accessories"),
    ("not_clothing", "a photograph of something that is not clothing, such as food, an animal, a building, a landscape, or an electronic device", "not_clothing"),
]

COLOR_PALETTE = {
    "Black": (20, 20, 20), "White": (245, 245, 240), "Grey": (128, 128, 128),
    "Navy": (25, 45, 85), "Blue": (50, 110, 190), "Red": (190, 45, 45),
    "Green": (55, 125, 75), "Yellow": (225, 195, 55), "Pink": (225, 145, 170),
    "Purple": (125, 80, 155), "Brown": (125, 80, 45), "Beige": (205, 185, 145),
    "Orange": (220, 125, 45),
}


class GarmentImageClassifier:
    def __init__(self, clip_service: Any):
        self.clip = clip_service
        self.torch = None
        self.head = None
        self.trained_labels: list[str] = []
        self.model_dir = Path(__file__).resolve().parent
        self._load_trained_head()

    @property
    def is_available(self) -> bool:
        return bool(self.clip.is_loaded and self.clip._model is not None and self.clip._processor is not None)

    def _load_trained_head(self) -> None:
        weights_path = self.model_dir / "garment_head.pt"
        labels_path = self.model_dir / "garment_labels.json"
        if not weights_path.exists() or not labels_path.exists():
            return
        try:
            import torch
            labels = json.loads(labels_path.read_text(encoding="utf-8"))
            model = torch.nn.Linear(512, len(labels))
            state = torch.load(weights_path, map_location="cpu", weights_only=True)
            model.load_state_dict(state)
            model.eval()
            self.torch = torch
            self.head = model
            self.trained_labels = labels
        except Exception:
            self.head = None
            self.trained_labels = []

    def classify(self, image: Image.Image) -> dict:
        if not self.is_available:
            raise RuntimeError("The image model is not available. Install the ML requirements and allow the CLIP checkpoint to download.")
        import torch

        image = image.convert("RGB")
        if self.head is not None:
            inputs = self.clip._processor(images=image, return_tensors="pt")
            with torch.no_grad():
                features = self.clip._model.get_image_features(**inputs)
                logits = self.head(features)
                probabilities = torch.softmax(logits[0], dim=-1)
            ranked = sorted(
                [(label, float(probabilities[i])) for i, label in enumerate(self.trained_labels)],
                key=lambda pair: pair[1], reverse=True
            )
            predictions = [{"label": label, "confidence": round(score, 4)} for label, score in ranked[:3]]
            label = ranked[0][0]
            confidence = ranked[0][1]
            mapping = {name: (name, category) for name, _, category in LABELS}
            subcategory, category = mapping.get(label, (label.replace("_", " ").title(), "other"))
        else:
            prompts = [entry[1] for entry in LABELS]
            inputs = self.clip._processor(text=prompts, images=image, return_tensors="pt", padding=True)
            with torch.no_grad():
                logits = self.clip._model(**inputs).logits_per_image[0]
                probabilities = torch.softmax(logits, dim=-1)
            ranked_indices = torch.argsort(probabilities, descending=True)[:3].tolist()
            predictions = [
                {"label": LABELS[i][0], "confidence": round(float(probabilities[i]), 4)}
                for i in ranked_indices
            ]
            best = ranked_indices[0]
            subcategory, _, category = LABELS[best]
            confidence = float(probabilities[best])

        not_clothing_score = next((p["confidence"] for p in predictions if p["label"] == "not_clothing"), 0.0)
        is_clothing = category != "not_clothing" and confidence >= 0.20 and confidence > not_clothing_score
        if not is_clothing:
            category = "not_clothing"
            subcategory = "Not clothing / unsupported image"

        rgb = image.resize((48, 48)).convert("RGB")
        pixels = list(rgb.getdata())
        mean = tuple(round(sum(pixel[channel] for pixel in pixels) / len(pixels)) for channel in range(3))
        color_name = min(COLOR_PALETTE, key=lambda name: sum((mean[i] - COLOR_PALETTE[name][i]) ** 2 for i in range(3)))
        color_hex = "#{:02X}{:02X}{:02X}".format(*mean)

        return {
            "category": category,
            "subcategory": subcategory.replace("_", " ").title(),
            "dominant_color": color_name,
            "color_hex": color_hex,
            "pattern": "Unknown",
            "style_tags": [],
            "suitable_seasons": [],
            "confidence_score": round(confidence, 4),
            "is_clothing": is_clothing,
            "needs_review": (not is_clothing) or confidence < 0.40,
            "top_predictions": predictions,
            "model_type": "supervised_clip_head" if self.head is not None else "clip_zero_shot",
        }
