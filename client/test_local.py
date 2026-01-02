import base64
import requests
import os
from dotenv import load_dotenv
load_dotenv()

from auth import auth_headers   # 認証ヘッダー取得関数

API_URL = os.environ.get("VISION_API_URL", "http://localhost:8080").strip()
print("Using API_URL =", API_URL)

# 実行場所に依存しないようにする（おすすめ）
BASE_DIR = os.path.dirname(__file__)
IMAGE_FILE = os.path.join(BASE_DIR, "my_face.jpg")

MODE = "face"  # label / ocr / face

def main():
    if not os.path.exists(IMAGE_FILE):
        print(f"エラー: {IMAGE_FILE} が見つかりません。")
        return

    with open(IMAGE_FILE, "rb") as image_file:
        base64_data = base64.b64encode(image_file.read()).decode("utf-8")

    payload = {"image_base64": base64_data, "mode": MODE}

    print(f"画像を送信中... ({MODE}モード)")
    try:
        # ★ここが重要：headers を付ける
        response = requests.post(API_URL, json=payload, headers=auth_headers(), timeout=30)

        if response.status_code == 200:
            data = response.json()
            print("\n--- 判定結果 ---")
            for item in data.get("results", []):
                print(f"・{item.get('description','')} ({item.get('score','')})")
        else:
            print(f"エラー: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"通信エラー: {e}")

if __name__ == "__main__":
    main()
