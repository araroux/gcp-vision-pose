import base64
import requests
import os

# --- 設定 ---
# あなたのCloud RunのURLに書き換えてください
API_URL = "https://my-vision-service-593396693760.asia-northeast1.run.app"
# テストする画像ファイル名 (同じフォルダに置いてください)
#IMAGE_FILE = "my_photo.jpg" 
IMAGE_FILE = "my_face.jpg" 

# モード: label, ocr, face
#MODE = "label" 
#MODE = "ocr" 
MODE = "face" 

def main():
    # 1. ローカルの画像ファイルを読み込んでBase64に変換
    if not os.path.exists(IMAGE_FILE):
        print(f"エラー: {IMAGE_FILE} が見つかりません。")
        return

    with open(IMAGE_FILE, "rb") as image_file:
        # バイナリを読み込んでBase64文字列に変換
        base64_data = base64.b64encode(image_file.read()).decode('utf-8')

    # 2. サーバーに送信 (URLではなく、image_base64を送る)
    payload = {
        "image_base64": base64_data,
        "mode": MODE
    }

    print(f"画像を送信中... ({MODE}モード)")
    try:
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- 判定結果 ---")
            for item in data.get('results', []):
                print(f"・{item['description']} ({item['score']})")
        else:
            print(f"エラー: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"通信エラー: {e}")

if __name__ == "__main__":
    main()