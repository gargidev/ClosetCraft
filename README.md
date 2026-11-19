# Closet Craft

> **Your Wardrobe. Your Style. Your Outfit.**

Closet Craft is an AI-assisted digital wardrobe and outfit planning application. Upload garment photos, classify clothing from image content, organize clean and laundry items, and build outfit combinations from your own wardrobe.

## Repository

- GitHub: https://github.com/gargidev/ClosetCraft
- [Anti-Gravity implementation prompt](docs/ANTIGRAVITY_PROMPT.md)
- [Deployment and ML training guide](docs/DEPLOYMENT.md)
- [Garment dataset and training instructions](ml-service/data/README.md)

## Features and architecture

- **Frontend:** React, TypeScript, Vite, Tailwind CSS.
- **Backend:** Node.js, Express, TypeScript, Zod.
- **ML service:** FastAPI, CLIP ViT-B/32 image/text embeddings, outfit-ranking engine, optional supervised classification head.
- **Database:** PostgreSQL and Prisma schema are included; check the deployment guide for the current persistence implementation caveat.
- **Local orchestration:** Docker Compose.

### Garment classification

The ML service exposes `POST /classify-garment` and classifies decoded image pixels, not filenames. It returns garment category, subcategory, colour estimate, confidence, candidate labels, and a review flag. It rejects malformed image data and does not fetch arbitrary remote URLs.

The default classifier uses CLIP zero-shot image/text similarity when the checkpoint is available. A supervised classification head can be trained with a properly labelled, appropriately licensed dataset using `ml-service/train_classifier.py`. **No supervised model weights or training accuracy are included or claimed by this repository until an actual training run has been completed.**

## Run locally

1. Copy `.env.example` to `.env` and replace development secrets with unique local values.
2. Start the stack:

```bash
docker compose up --build
```

3. Open:
   - Frontend: http://localhost:3000
   - Backend health: http://localhost:4000/api/health
   - ML health: http://localhost:8000/health

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for environment variables, model training, and public hosting steps.

## ML training

Follow [ml-service/data/README.md](ml-service/data/README.md) to arrange licensed training and validation images. Then:

```bash
cd ml-service
pip install -r requirements.txt
python train_classifier.py --data-dir ./data/dataset --epochs 8 --batch-size 16
```

The script saves the trained head, class labels, and validation metrics under `ml-service/app/models/`. Review the metrics and test on independent images before using it in a demonstration.

## Deployment (strict $0 budget)

The repository includes a [Vercel frontend preview configuration](vercel.json). Follow [the zero-billing deployment guide](docs/FREE_DEPLOYMENT.md) before deploying.

**Important:** This configuration deploys only the React/Vite frontend preview. The current Express API uses in-memory Maps, the Prisma schema is not wired into route handlers, Supabase Storage is not integrated, and the separate PyTorch ML service is not hosted by Vercel. Do not treat the preview as a complete working production app.

Google Cloud Run and the previous paid Render Blueprint have been intentionally removed from the deployment path because a strict no-charge requirement cannot be guaranteed by metered hosting.

## Security

- Never commit `.env`, database passwords, API keys, service-account files, or model-dataset credentials.
- Use a unique production JWT secret.
- Restrict CORS to the deployed frontend origin.
- Use private networking between backend and ML service where available.
- Keep garment records scoped to the authenticated user.
