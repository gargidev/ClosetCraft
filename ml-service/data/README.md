# Garment classifier dataset

Place a properly licensed fashion dataset here using this structure:

```
dataset/
  train/
    t_shirt/
    shirt/
    blouse/
    jeans/
    trousers/
    skirt/
    shorts/
    dress/
    jacket/
    shoes/
    bags/
    accessories/
    not_clothing/
  val/
    (the same class folders)
```

- Keep train and validation images separate; do not place the same image in both.
- Include varied backgrounds, lighting, garment colours, poses, folds, and product-photo styles.
- Include genuinely unrelated images in `not_clothing` so the classifier can learn rejection.
- Keep a dataset source, licence, and any preprocessing notes in your project report.
- Do not redistribute a dataset unless its licence permits it.

Train from the `ml-service` directory:

```bash
python train_classifier.py --data-dir ./data/dataset --epochs 8 --batch-size 16
```

The script uses a frozen CLIP ViT-B/32 image encoder and trains a supervised linear classification head. It writes `app/models/garment_head.pt`, `app/models/garment_labels.json`, and `app/models/training_metrics.json`. The inference service loads the saved head automatically. Until those files exist, it uses CLIP zero-shot image/text similarity; that is inference, not supervised training.
