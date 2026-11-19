# Anti-Gravity Build Prompt — Closet Craft

You are working inside the existing GitHub repository `gargidev/ClosetCraft`. Do not replace the project with a fresh template. First inspect the current codebase, preserve working features, and then implement the requirements below in the existing architecture.

## Product goal

Build **Closet Craft**, a polished, formal, AI-powered digital wardrobe. A user uploads clothing photos, the ML service identifies each item, the item is saved in the user's wardrobe, and the user can create outfits by dragging one top-wear item and one bottom-wear item into two selection slots. The wardrobe also tracks whether each garment is available, in laundry, drying, or otherwise unavailable.

This must be a functioning full-stack application, not a static mockup. Do not show fake success states or claim that an ML model has run when it has not.

## Existing architecture to preserve and complete

- Frontend: React, TypeScript, Vite, Tailwind CSS.
- Backend: Node.js, Express, TypeScript, Zod.
- ML service: Python, FastAPI, PyTorch, Hugging Face Transformers / CLIP.
- Data layer: PostgreSQL and Prisma schema are present; verify that runtime routes actually use persistent storage before claiming persistence.
- Local development: Docker Compose.

Before coding:
1. Inspect the repository tree, current routes, schemas, API client, UI pages, Docker files, and tests.
2. Identify broken or disconnected flows, especially upload/classification, garment persistence, outfit generation, and laundry status.
3. Make a short implementation plan and then implement it.
4. Do not remove existing functionality or overwrite unrelated files.

## 1. Formal frontend design

Create a clean, professional fashion-tech interface:
- Neutral palette: ivory, white, charcoal, warm grey, muted sage, and restrained accent colours.
- Strong typography, consistent spacing, polished cards, subtle shadows, and restrained motion.
- Responsive desktop, tablet, and mobile layouts.
- Accessible labels, keyboard navigation, focus states, and clear empty/loading/error states.
- Keep the visual design formal and uncluttered. Avoid childish gradients, excessive emojis, and overly playful styling.

Dashboard navigation:
- Dashboard
- My Wardrobe
- Add Clothes
- Create Outfit
- Laundry Tracker
- Saved Outfits / Outfit History
- Profile / Preferences

Dashboard metrics: total garments, available garments, laundry items, and saved outfits.

## 2. Real image upload and ML classification

Support drag-and-drop and file-picker uploads for JPG, JPEG, PNG, and WEBP. Allow multiple uploads, but classify each image independently.

The image must be sent to the Python ML service as image bytes/base64. Never classify from the filename, file extension, alt text, or a user-entered name.

The ML service must:
- Validate image decoding and reject corrupt/unsupported files.
- Determine whether the image contains a clothing/fashion item.
- Predict a garment subcategory and normalized category.
- Return confidence and the top candidate labels.
- Return an explicit invalid/non-clothing result for objects, animals, screenshots, landscapes, and unrelated images.
- Mark low-confidence or ambiguous predictions as needing user review.
- Never invent a confident category when the model is unavailable; return a clear service-unavailable error instead.

Required categories and examples:
- tops: T-shirt, shirt, blouse, tank top, hoodie, sweater, kurti
- bottoms: jeans, trousers, pants, shorts, skirt, leggings
- dresses: dress, gown, jumpsuit
- outerwear: jacket, coat, blazer
- shoes: sneakers, heels, boots, sandals
- bags: backpack, handbag, tote
- accessories: belt, scarf, jewellery, sunglasses
- not_clothing: non-clothing / unsupported image

Show a review step after classification:
- Image preview
- Predicted category and subcategory
- Confidence percentage
- Alternative predictions
- Manual category correction
- Confirm and save / discard

Do not use Fashion-MNIST alone for this task; it has too few coarse classes. Use a suitably licensed multi-class fashion dataset for supervised fine-tuning. Keep dataset provenance and licence details in documentation.

## 3. Wardrobe memory and persistence

After the user confirms a classification, save:
- garment ID and owner ID
- original image URL or durable storage reference
- normalized category and subcategory
- detected colour and optional pattern/material
- ML confidence and whether the user corrected the prediction
- laundry/availability status
- created and updated timestamps

Use the persistent database and durable image storage. Do not use in-memory Maps as production persistence. Ensure every query is scoped to the authenticated user. Never expose one user's wardrobe to another user.

The wardrobe must survive browser refreshes, server restarts, and redeployments.

## 4. Availability and laundry tracker

Every garment has a status:
- AVAILABLE / CLEAN — eligible for outfit generation
- WORN — not eligible until changed back to clean
- IN_LAUNDRY / WASHING
- DRYING
- UNAVAILABLE
- DAMAGED

Allow the user to change status from the wardrobe item card and laundry tracker. Record status changes where supported.

Hard rule: only AVAILABLE/CLEAN/READY_TO_WEAR garments can be selected or recommended. Laundry, drying, worn, unavailable, and damaged garments must never appear in generated outfit selections. Enforce this in the backend/ML service, not just by hiding buttons in the UI.

## 5. Drag-and-drop outfit builder

Build a dedicated **Create Your Outfit** workspace with two clearly labelled drop zones:

**Top Wear**
Accept tops such as T-shirts, shirts, blouses, hoodies, sweaters, and kurtis.

**Bottom Wear**
Accept bottoms such as pants, jeans, trousers, skirts, shorts, and leggings.

Users can:
- Drag wardrobe cards into the matching drop zone.
- Click a garment to select it as an accessible alternative to dragging.
- Remove or replace a selected item.
- See a combined outfit preview.

Validate each drop:
- Top in Top Wear: accept.
- Bottom in Bottom Wear: accept.
- Two tops: reject the second item with a helpful message.
- Two bottoms: reject the second item with a helpful message.
- Dress: offer a separate one-piece outfit mode, not a top/bottom pairing.
- Laundry/unavailable item: reject and explain why.
- Invalid or unclassified item: require classification confirmation first.

## 6. Outfit recommendation

After one valid top and one valid bottom are selected:
- Check that both garments belong to the current user.
- Check their categories and availability again on the backend.
- Evaluate colour harmony, style, occasion, mood, weather/season if supplied, and user preferences.
- Return a match score with a transparent explanation.
- Display the selected clothing images together as a clean outfit preview.

Example result:

"Your Outfit for Today"
- Top: Black T-shirt
- Bottom: Blue jeans
- Style: Casual
- Occasion: Everyday / College
- Why it works: "The neutral black top balances the blue denim for a simple, versatile casual look."

Actions:
- Save Outfit
- Generate Another Combination
- Replace Top
- Replace Bottom
- View Details

Also support automatic outfit suggestions from all eligible wardrobe items. Never include the same garment twice in one outfit and avoid repeating recently worn combinations where history exists.

## 7. Testing and quality

Add or update tests for:
- Valid T-shirt image classification
- Valid pants/skirt image classification
- Non-clothing image rejection
- Corrupt image rejection
- Low-confidence manual review
- Same-category drop rejection
- Top + bottom accepted
- Dress one-piece mode
- Laundry/drying/unavailable hard exclusion
- User ownership checks
- Persistent wardrobe records
- Outfit generation and saving

Run frontend build, backend typecheck/tests, and ML pytest suite. Fix failures caused by your changes. Document any checks that cannot be run and why.

## 8. Deployment

Prepare deployment configuration for the complete stack (frontend, backend, ML service, and PostgreSQL). Keep secrets out of Git. Use environment variables and provide an `.env.example` with safe placeholders only.

Add a deployment guide to README with:
- required environment variables
- database setup/migrations
- ML model download/training steps
- service start commands
- health-check URLs
- exact provider steps to create a public deployment

Do not put a fake live URL in the README. Only add a live application URL after the provider confirms a successful deployment. A deployment button may link to the provider's blueprint setup, but label it as a deployment setup link, not a live demo.

## 9. Deliverables

- Complete working application integrated into the existing repository.
- Real image-based classification endpoint.
- Reproducible supervised training script and dataset instructions.
- Persistent wardrobe and laundry management.
- Drag-and-drop top/bottom outfit builder.
- Outfit recommendation and history.
- Tests and setup documentation.
- Updated README and deployment configuration.

Work incrementally, preserve existing code, and report honestly which parts are implemented, tested, trained, and deployed. Never claim that a model has been trained unless training actually completed and the resulting weights are saved and referenced by the inference service.
