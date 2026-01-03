"""
Pose Landmark API (Cloud Run + ID token auth)

Requires (local test):
- Google Cloud SDK installed
- `gcloud auth login` executed  (only if your client fetches ID token locally)

This server itself does NOT call Google Cloud Vision API anymore.
"""

import os
import base64
import requests
from flask import Flask, request, jsonify

from pose_detector import PoseDetector

app = Flask(__name__)

# =========================
# Env-config (Cloud Run)
# =========================
ALLOW_IMAGE_URL = os.environ.get("ALLOW_IMAGE_URL", "false").lower() == "true"
HTTP_TIMEOUT_SEC = float(os.environ.get("HTTP_TIMEOUT_SEC", "10"))
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", "8000000"))  # 8MB default

# Create once (avoid per-request init cost)
pose_detector = PoseDetector()

# Optional: fixed UA header for URL fetch
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


def _estimate_b64_bytes(b64_str: str) -> int:
    """Roughly estimate decoded bytes from base64 length (guard before decoding)."""
    padding = b64_str.count("=")
    return max(0, (len(b64_str) * 3) // 4 - padding)


def _get_image_bytes_from_request_json(data):
    """Return (image_bytes, error_response_tuple_or_None)."""
    image_b64 = data.get("image_base64")
    image_uri = data.get("url")

    if image_b64:
        est = _estimate_b64_bytes(image_b64)
        if est > MAX_IMAGE_BYTES:
            return None, (jsonify({"error": f"image too large (>{MAX_IMAGE_BYTES} bytes)"}), 413)

        try:
            content = base64.b64decode(image_b64, validate=True)
        except Exception:
            return None, (jsonify({"error": "invalid base64 in image_base64"}), 400)

        if len(content) > MAX_IMAGE_BYTES:
            return None, (jsonify({"error": f"image too large (>{MAX_IMAGE_BYTES} bytes)"}), 413)

        return content, None

    if image_uri:
        if not ALLOW_IMAGE_URL:
            return None, (jsonify({"error": "URL input is disabled"}), 400)

        try:
            img_response = requests.get(
                image_uri,
                headers=DEFAULT_HEADERS,
                timeout=HTTP_TIMEOUT_SEC,
            )
        except requests.RequestException as e:
            return None, (jsonify({"error": f"failed to download image: {str(e)}"}), 400)

        if img_response.status_code != 200:
            return None, (jsonify({"error": f"failed to download image (status: {img_response.status_code})"}), 400)

        content = img_response.content
        if len(content) > MAX_IMAGE_BYTES:
            return None, (jsonify({"error": f"image too large (>{MAX_IMAGE_BYTES} bytes)"}), 413)

        return content, None

    return None, (jsonify({"error": "image_base64 or url is required"}), 400)


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.post("/detect")
def detect_pose():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    content, err = _get_image_bytes_from_request_json(data)
    if err:
        return err

    try:
        result = pose_detector.detect_from_bytes(content)
        return jsonify({
            "mode": "pose",
            "image_size": {"width": result.width, "height": result.height},
            "landmarks": result.landmarks,
            "inference_ms": result.inference_ms,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Cloud Run uses $PORT
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
