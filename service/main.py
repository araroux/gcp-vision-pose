import os
import base64
import requests
from flask import Flask, request, jsonify
from google.cloud import vision

app = Flask(__name__)

# =========================
# Env-config (Cloud Run)
# =========================
ALLOW_IMAGE_URL = os.environ.get("ALLOW_IMAGE_URL", "false").lower() == "true"
HTTP_TIMEOUT_SEC = float(os.environ.get("HTTP_TIMEOUT_SEC", "10"))
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", "8000000"))  # 8MB default

# Vision client (create once)
vision_client = vision.ImageAnnotatorClient()

# Optional: fixed UA header for URL fetch
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

def _estimate_b64_bytes(b64_str: str) -> int:
    """
    Roughly estimate decoded bytes from base64 length.
    This prevents huge payloads before decoding.
    """
    # base64 length * 3/4 minus padding is close enough for a guard
    padding = b64_str.count("=")
    return max(0, (len(b64_str) * 3) // 4 - padding)

@app.route("/", methods=["POST"])
def analyze_image():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    image_b64 = data.get("image_base64")
    image_uri = data.get("url")
    mode = data.get("mode", "label")

    content = None

    try:
        # -------------------------
        # 1) Get image bytes
        # -------------------------
        if image_b64:
            # Size guard before decoding
            est = _estimate_b64_bytes(image_b64)
            if est > MAX_IMAGE_BYTES:
                return jsonify({"error": f"image too large (>{MAX_IMAGE_BYTES} bytes)"}), 413

            try:
                content = base64.b64decode(image_b64, validate=True)
            except Exception:
                return jsonify({"error": "invalid base64 in image_base64"}), 400

            # Size guard after decoding (strict)
            if len(content) > MAX_IMAGE_BYTES:
                return jsonify({"error": f"image too large (>{MAX_IMAGE_BYTES} bytes)"}), 413

        elif image_uri:
            if not ALLOW_IMAGE_URL:
                return jsonify({"error": "URL input is disabled"}), 400

            # Fetch image with timeout
            try:
                img_response = requests.get(
                    image_uri,
                    headers=DEFAULT_HEADERS,
                    timeout=HTTP_TIMEOUT_SEC,
                )
            except requests.RequestException as e:
                return jsonify({"error": f"failed to download image: {str(e)}"}), 400

            if img_response.status_code != 200:
                return jsonify({
                    "error": f"failed to download image (status: {img_response.status_code})"
                }), 400

            content = img_response.content
            if len(content) > MAX_IMAGE_BYTES:
                return jsonify({"error": f"image too large (>{MAX_IMAGE_BYTES} bytes)"}), 413

        else:
            return jsonify({"error": "image_base64 or url is required"}), 400

        # -------------------------
        # 2) Call Vision API
        # -------------------------
        image = vision.Image(content=content)
        results = []

        if mode == "label":
            response = vision_client.label_detection(image=image)
            for label in response.label_annotations:
                results.append({
                    "description": label.description,
                    "score": f"{label.score:.2%}"
                })

        elif mode == "ocr":
            response = vision_client.text_detection(image=image)
            texts = response.text_annotations
            if texts:
                clean_text = texts[0].description.replace("\n", " ")
                results.append({"description": clean_text, "score": "N/A"})
            else:
                results.append({"description": "文字なし", "score": ""})

        elif mode == "face":
            response = vision_client.face_detection(image=image)
            faces = response.face_annotations
            likelihood_name = ("不明", "極低い", "低い", "中程度", "高い", "極高い")
            if not faces:
                results.append({"description": "顔なし", "score": ""})
            else:
                for i, face in enumerate(faces):
                    results.append({
                        "description": f"顔#{i+1} 笑顔: {likelihood_name[face.joy_likelihood]}",
                        "score": f"確信度: {face.detection_confidence:.2%}"
                    })

        else:
            return jsonify({"error": "unsupported mode"}), 400

        if response.error.message:
            return jsonify({"error": response.error.message}), 500

        return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Cloud Run uses $PORT
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
