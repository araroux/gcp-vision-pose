# GCP Pose Landmark PoC (Cloud Run + Simple Clients)

## Overview
This repository provides a simple Pose Landmark detection API running on **Cloud Run**.
The server uses **MediaPipe Pose** and returns landmark coordinates from an input image.

## Architecture
client (PowerShell / Python) -> Cloud Run (Flask + gunicorn) -> MediaPipe Pose

## Directories
- `service/` : Cloud Run service (Flask API)
- `client/`  : Python clients (GUI + CLI)

## API

### Health Check
- `GET /healthz`

Response:
```json
{ "status": "ok" }
````

### Detect Pose

* `POST /detect`

#### Request JSON

Either `image_base64` or `url` is required.

* `image_base64` (string, optional): base64 encoded image bytes
* `url` (string, optional): image URL (only when URL input is enabled)
* `mode` (optional): ignored by the current server (kept only for client compatibility)

Notes:

* URL input is **disabled by default**. To enable it, set `ALLOW_IMAGE_URL=true` on Cloud Run.
* Image size is limited by `MAX_IMAGE_BYTES` (default 8MB).

Example:

```json
{
  "image_base64": "...."
}
```

#### Response JSON

```json
{
  "mode": "pose",
  "image_size": { "width": 467, "height": 700 },
  "landmarks": [
    { "id": 0, "name": "NOSE", "x": 0.49, "y": 0.23, "z": -0.12, "visibility": 0.99 }
  ],
  "inference_ms": 113
}
```

## Authentication (Cloud Run)

This service is intended to run on Cloud Run with **authentication enabled**.
Clients must attach a valid **Google Cloud ID token** as a Bearer token.

* Unauthenticated requests will be rejected (typically 401/403).
* For local testing (`http://localhost:8080`), authentication is not required.

## Deploy (PowerShell)

### 1) Set project/region (first time)

```powershell
gcloud auth login
gcloud config set project my-project-002-483111
gcloud config set run/region asia-northeast1
```

### 2) Build & Run locally

```powershell
cd .\service
docker build -t gcp-vision-pose .
docker run --rm -p 8080:8080 gcp-vision-pose
```

### 3) Push to Artifact Registry & Deploy to Cloud Run

```powershell
$PROJECT="my-project-002-483111"
$REGION="asia-northeast1"
$REPO="cloud-run-repo"
$SERVICE="gcp-vision-pose"
$IMAGE="$REGION-docker.pkg.dev/$PROJECT/$REPO/$SERVICE"

$TAG=(Get-Date -Format "yyyyMMdd-HHmmss")

docker tag $SERVICE "$IMAGE:$TAG"
docker push "$IMAGE:$TAG"

gcloud run deploy $SERVICE `
  --image "$IMAGE:$TAG" `
  --region $REGION `
  --platform managed `
  --no-allow-unauthenticated `
  --memory 2Gi `
  --cpu 1 `
  --timeout 60
```

### 4) Call Cloud Run with ID token

```powershell
$URL=(gcloud run services describe $SERVICE --region $REGION --format="value(status.url)")
$ID_TOKEN=(gcloud auth print-identity-token)
$headers=@{ Authorization="Bearer $ID_TOKEN" }

$b64=[Convert]::ToBase64String([IO.File]::ReadAllBytes(".\service\test.jpg"))
$body=@{ image_base64=$b64 } | ConvertTo-Json -Compress

Invoke-RestMethod -Method Post -Uri "$URL/detect" -Headers $headers -ContentType "application/json" -Body $body
```

## Client (Python)

### Install

```powershell
cd .\client
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Set API URL

Create `.env` in `client/`:

```env
VISION_API_URL=https://YOUR_CLOUD_RUN_URL
```

### Run (CLI)

```powershell
python .\test_local.py
```

### Run (GUI)

```powershell
python .\gui_file.py
```
