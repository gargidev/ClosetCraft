"""Train a supervised linear garment classifier on frozen CLIP image embeddings.

Expected directory structure:
  dataset/
    train/<class_name>/*.jpg
    val/<class_name>/*.jpg

Example class names: t_shirt, shirt, blouse, jeans, trousers, shorts, skirt,
leggings, dress, gown, jumpsuit, jacket, coat, blazer, sneakers, heels,
boots, sandals, handbag, backpack, scarf, belt, sunglasses, jewellery,
not_clothing.

Use only a dataset whose licence permits your intended use. The script does not
download datasets or claim training has happened; it saves weights only after
a successful run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from transformers import CLIPModel, CLIPProcessor

CHECKPOINT = "openai/clip-vit-base-patch32"


def collate(processor):
    def _collate(batch):
        images, labels = zip(*batch)
        images = [image.convert("RGB") for image in images]
        pixels = processor(images=images, return_tensors="pt")["pixel_values"]
        return pixels, torch.tensor(labels, dtype=torch.long)
    return _collate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, help="Folder containing train/ and val/ class folders")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--output-dir", default=str(Path(__file__).parent / "app" / "models"))
    args = parser.parse_args()

    root = Path(args.data_dir)
    train_data = ImageFolder(root / "train")
    val_data = ImageFolder(root / "val")
    if train_data.classes != val_data.classes:
        raise ValueError("train/ and val/ must contain exactly the same class folders")
    if len(train_data.classes) < 2:
        raise ValueError("At least two garment classes are required")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = CLIPProcessor.from_pretrained(CHECKPOINT)
    clip = CLIPModel.from_pretrained(CHECKPOINT).to(device)
    clip.eval()
    for parameter in clip.parameters():
        parameter.requires_grad = False

    head = nn.Linear(512, len(train_data.classes)).to(device)
    optimizer = torch.optim.AdamW(head.parameters(), lr=args.learning_rate)
    criterion = nn.CrossEntropyLoss()
    train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True, collate_fn=collate(processor))
    val_loader = DataLoader(val_data, batch_size=args.batch_size, shuffle=False, collate_fn=collate(processor))

    best_accuracy = 0.0
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)

    for epoch in range(args.epochs):
        head.train()
        total_loss = 0.0
        for pixels, labels in train_loader:
            pixels, labels = pixels.to(device), labels.to(device)
            with torch.no_grad():
                features = clip.get_image_features(pixel_values=pixels)
            logits = head(features)
            loss = criterion(logits, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item())

        head.eval()
        correct = count = 0
        with torch.no_grad():
            for pixels, labels in val_loader:
                pixels, labels = pixels.to(device), labels.to(device)
                features = clip.get_image_features(pixel_values=pixels)
                predictions = head(features).argmax(dim=1)
                correct += int((predictions == labels).sum().item())
                count += int(labels.numel())
        accuracy = correct / max(1, count)
        print(f"epoch={epoch + 1}/{args.epochs} loss={total_loss / max(1, len(train_loader)):.4f} val_accuracy={accuracy:.4f}")
        if accuracy >= best_accuracy:
            best_accuracy = accuracy
            torch.save(head.cpu().state_dict(), output / "garment_head.pt")
            head.to(device)
            (output / "garment_labels.json").write_text(json.dumps(train_data.classes, indent=2), encoding="utf-8")

    (output / "training_metrics.json").write_text(
        json.dumps({"validation_accuracy": best_accuracy, "classes": train_data.classes, "checkpoint": CHECKPOINT}, indent=2),
        encoding="utf-8",
    )
    print(f"Saved best classifier head to {output}; validation accuracy={best_accuracy:.4f}")


if __name__ == "__main__":
    main()
