# GCP Pose Landmark PoC (Cloud Run + Simple Clients)

## Overview

This repository is derived from `gcp-vision-test`.

It focuses on detecting body and face landmark coordinates
(e.g. pose keypoints, facial landmarks),
while keeping the same Cloud Run authentication and deployment design.

## Architecture
client -> Cloud Run (Flask+gunicorn) -> MediaPipe Pose

## Authentication

This service is deployed on Cloud Run with authentication enabled.
Clients must attach a valid Google Cloud ID token.

Unauthenticated requests will be rejected (403).

## API
### Endpoint
- `POST /`

### Request JSON
- `image_base64` (string, optional): base64 encoded image bytes
- `url` (string, optional): image URL (fallback)
- `mode` (string, optional): `label` | `ocr` | `face` (default: `label`)

Either `image_base64` or `url` is required.

### Response JSON
```json
{
  "results": [
    {"description": "...", "score": "..."}
  ]
}
