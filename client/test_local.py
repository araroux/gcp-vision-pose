import base64
import requests
import os
from dotenv import load_dotenv
load_dotenv()
from client.auth import auth_headers

API_URL = os.environ.get("VISION_API_URL", "http://localhost:8080").strip()
DETECT_ENDPOINT = f"{API_URL}/detect"
print("Using API_URL =", API_URL)

# 実行場所に依存しないようにする（おすすめ）
BASE_DIR = os.path.dirname(__file__)
IMAGE_FILE = os.path.join(BASE_DIR, "test_image.jpg")

def main():
    if not os.path.exists(IMAGE_FILE):
        print(f"エラー: {IMAGE_FILE} が見つかりません。")
        print(f"姿勢検出のテストには人物が写っている画像を {IMAGE_FILE} として配置してください。")
        return

    with open(IMAGE_FILE, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode("utf-8")

    payload = {"image_base64": base64_data}

    print("画像を送信中... (Pose Detection)")
    try:
        response = requests.post(DETECT_ENDPOINT, json=payload, headers=auth_headers(API_URL), timeout=30)

        if response.status_code == 200:
            data = response.json()
            print("\n--- 検出結果 ---")
            print(f"画像サイズ: {data.get('image_size', {}).get('width')}x{data.get('image_size', {}).get('height')}")
            print(f"推論時間: {data.get('inference_ms', 0)}ms")

            landmarks = data.get("landmarks", [])
            print(f"ランドマーク数: {len(landmarks)}")

            if landmarks:
                print("\n主要なランドマーク:")
                key_landmarks = ["NOSE", "LEFT_SHOULDER", "RIGHT_SHOULDER",
                               "LEFT_ELBOW", "RIGHT_ELBOW", "LEFT_WRIST", "RIGHT_WRIST",
                               "LEFT_HIP", "RIGHT_HIP", "LEFT_KNEE", "RIGHT_KNEE"]
                for lm in landmarks:
                    if lm.get("name") in key_landmarks:
                        name = lm.get("name", "")
                        x = lm.get("x", 0)
                        y = lm.get("y", 0)
                        vis = lm.get("visibility", 0)
                        print(f"  {name}: ({x:.3f}, {y:.3f}) 信頼度:{vis:.2f}")
            else:
                print("姿勢が検出されませんでした")
        else:
            print(f"エラー: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"通信エラー: {e}")

if __name__ == "__main__":
    main()
