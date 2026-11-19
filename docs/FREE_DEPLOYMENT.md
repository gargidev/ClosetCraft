# Zero-billing deployment plan (Closet Craft)

## Cost rule

This setup intentionally does **not** create Google Cloud resources, enable billing, attach a payment method, or configure any pay-as-you-go service. Do not add a credit card to a hosting provider for this project if the requirement is that charges must be impossible.

A hosted free tier is still subject to provider terms, quotas, pauses, and product changes. No third-party service can guarantee permanent availability at zero cost.

## What is configured now

- **Vercel Hobby:** the React/Vite frontend can be deployed as a static site from this repository. Hobby is intended for personal, non-commercial use. If the project is used commercially, do not use this plan.
- **Supabase Free:** intended PostgreSQL and Storage provider. Create a free project manually and do not add a paid plan or payment method.
- **Google Cloud Run:** deliberately not configured. Cloud Run requires a billing account; its free usage allowance is not a hard guarantee of zero charges.
- **PyTorch ML service:** not deployed to a paid or metered host. The current ML service needs a compatible Python runtime and model memory. This repository does not yet contain a verified, no-billing production host for it.

## Important current application limitations

This repository is **not yet ready for a complete production deployment**:

1. The current Express API stores users, garments, outfits, favorites, and other records in in-memory JavaScript Maps. These records disappear when the server process restarts and are not stored in the included Prisma schema.
2. The Prisma PostgreSQL schema exists, but the current route handlers are not wired to Prisma/Supabase persistence.
3. The frontend calls `/api/...`, but this Vercel configuration only publishes the frontend static build; it does not magically host the Express API.
4. Garment image classification and outfit recommendations call the separate FastAPI ML service. That service is not hosted by this static frontend deployment.
5. Supabase Storage is not yet integrated into the upload flow.

Therefore, a Vercel deployment from this configuration is a **frontend preview only**. Login, saving garments, persistent wardrobe data, image classification, and ML recommendations must not be represented as production-ready until the backend, database, storage, and ML paths have been implemented and tested.

## Deploy the frontend preview

1. Create a Vercel account using the free Hobby plan.
2. Import `gargidev/ClosetCraft` from GitHub.
3. Keep the project root at the repository root. The committed `vercel.json` builds `frontend/` and publishes `frontend/dist`.
4. Do not select a paid plan, add a card, enable paid add-ons, or add metered services.
5. Deploy. The generated Vercel URL is a frontend preview, not the complete working app.

## Supabase setup (manual, free plan only)

1. Create a Supabase project on the Free plan.
2. Do not upgrade or add billing details.
3. Keep the project within the published Free limits; free projects may be paused after inactivity.
4. Do not paste the Supabase service-role key into frontend variables or commit any secret.
5. The repository needs a separate implementation change to connect the Express routes and image upload flow to Supabase before the app can use the database and Storage.

## Next engineering work required for a complete zero-billing-cap design

- Replace in-memory Maps in every Express route with durable Supabase/PostgreSQL queries and enforce user ownership in the database.
- Implement Supabase Storage upload and signed/public image URL handling.
- Host the API only on a provider plan that is explicitly hard-capped at $0 and does not require a billing method, or migrate the API routes to an eligible free serverless platform after verifying its current limits.
- Move garment inference into the browser (for example, a small ONNX model running with WebAssembly/WebGPU) or identify a genuinely free, non-metered CPU inference host. Do not use Cloud Run under the strict no-charge requirement.
- Add automated build, API, auth, persistence, upload, and ML tests.
- Verify all flows before describing the site as fully deployed.

## Live status

No live URL is verified by this repository change. The Vercel URL will only exist after the owner imports the repository and deploys it. Even then, it will be a frontend preview until the backend and ML integration work above is complete.
