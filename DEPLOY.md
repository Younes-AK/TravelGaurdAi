# Deploying a live demo (Render)

This app has two parts that need to be deployed separately:

- **Backend** — FastAPI decision API (`backend/`), built from the root `Dockerfile`
- **Frontend** — React/Vite dashboard (`frontend/`), a static site that calls the backend

The backend defaults to `CAMARA_PROVIDER=mock`, so it works fully out of the box for a demo — no telecom API keys required.

## 1. Deploy the backend

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**
2. Connect your GitHub account and select the `TravelGaurdAi` repo
3. Configure:
   - **Root Directory**: leave blank (Dockerfile is at repo root)
   - **Environment**: `Docker` (Render auto-detects the `Dockerfile`)
   - **Instance Type**: Free
4. Click **Create Web Service** and wait for the build/deploy to finish
5. Copy the URL Render gives you, e.g. `https://travelguard-api.onrender.com`
6. Verify it works: open `https://travelguard-api.onrender.com/docs` (Swagger UI) and `/health`

## 2. Lock down CORS (optional but recommended)

Once you have the frontend URL (step 3 below), go back to the backend service → **Environment** and add:

| Key | Value |
|---|---|
| `CORS_ALLOWED_ORIGINS` | `https://<your-frontend-url>.onrender.com` |

Without this, the API defaults to allowing all origins (`*`), which is fine for a demo but not for production.

## 3. Deploy the frontend

1. **New +** → **Static Site** → select the same repo
2. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm ci && npm run build`
   - **Publish Directory**: `dist`
3. Add an environment variable:

   | Key | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://travelguard-api.onrender.com` (the backend URL from step 1) |

4. Click **Create Static Site** and wait for the build

Render will give you a URL like `https://travelguard-ai-dashboard.onrender.com` — that's your shareable demo link.

## Notes

- Free-tier Render web services spin down after inactivity; the first request after idling can take ~30–60s to wake up. Fine for an occasional demo link, mention it if sharing widely.
- Every push to the connected branch auto-redeploys both services.
- To point the demo at real telecom data instead of mocked signals, set `CAMARA_PROVIDER=open_gateway` (or `nokia`) plus the corresponding `NAC_*` credentials on the backend service.
