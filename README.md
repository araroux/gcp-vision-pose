# GCP Vision API PoC (Cloud Run + Simple Clients)

## Overview
A minimal PoC that exposes Google Cloud Vision API features via a Cloud Run endpoint.
Supported modes:
- `label`: label detection
- `ocr`: text detection (OCR)
- `face`: face detection (joy likelihood + detection confidence)

## Architecture
client (GUI/CLI) -> Cloud Run (Flask + gunicorn) -> Google Cloud Vision API

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
