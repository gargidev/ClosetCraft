# Closet Craft deployment

## Important status

The repository contains deployment-ready Dockerfiles and a Docker Compose stack. A live public deployment is **not yet configured or verified**. Do not use the old fork owner's demo URL as this project's deployment URL.

## Local run

1. Copy `.env.example` to `.env` and set a unique JWT secret and a real PostgreSQL URL.
2. Run `docker compose up --build`.
3. Frontend: http://localhost:3000
4. Backend health: http://localhost:4000/api/health
5. ML health: http://localhost:8000/health

## ML image classifier

The inference endpoint is `POST /classify-garment`. Send JSON containing `image_base64_or_url` as a base64-encoded image or a `data:image/...;base64,...` data URL. Arbitrary remote URLs are not fetched to avoid SSRF risks.

The service uses CLIP ViT-B/32 zero-shot image/text similarity when the checkpoint is available. This is genuine image-based inference, but it is **not supervised fine-tuning**. To train a supervised garment head, follow [ml-service/data/README.md](../ml-service/data/README.md) and run:

```bash
cd ml-service
pip install -r requirements.txt
python train_classifier.py --data-dir ./data/dataset --epochs 8
```

Training requires a correctly labelled, appropriately licensed dataset. The trained head is saved under `ml-service/app/models` and loaded on service startup. No trained weights or validation accuracy are claimed until a real training run completes.

## Public deployment

Deploy each Docker service separately on a provider that supports Docker and private service networking:
- PostgreSQL managed database
- ML service using `ml-service/Dockerfile`, port 8000
- Backend using `backend/Dockerfile`, port 4000; set `DATABASE_URL`, `ML_SERVICE_URL`, `JWT_SECRET`, `FRONTEND_URL`
- Frontend using `frontend/Dockerfile`, port 80; configure the API proxy to the backend's private service hostname

Set secrets in the provider dashboard, never in Git. Run Prisma migrations against the managed database before routing traffic. Verify all three health endpoints and perform a real image upload before publishing the public URL.

The existing backend includes in-memory store/route implementations in parts of the codebase; verify and complete the database adapter migration before treating multi-instance production deployment as durable. A Docker Compose file alone does not create a public hosted deployment.
