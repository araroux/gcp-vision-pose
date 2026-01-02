import os
import base64
import requests
from flask import Flask, request, jsonify
from google.cloud import vision

app = Flask(__name__)

@app.route('/', methods=['POST'])
def analyze_image():
    data = request.get_json()
    
    # 1. Base64データがあるか確認
    image_b64 = data.get('image_base64')
    # 2. なければURLがあるか確認
    image_uri = data.get('url')
    
    mode = data.get('mode', 'label')

    content = None

    try:
        # --- 画像データの取得処理 ---
        if image_b64:
            # Base64文字列をバイナリデータに戻す
            content = base64.b64decode(image_b64)
        
        elif image_uri:
            # 既存のURLダウンロード処理（バックアップとして残す）
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            img_response = requests.get(image_uri, headers=headers)
            if img_response.status_code != 200:
                return jsonify({'error': f'画像のダウンロードに失敗しました (Status: {img_response.status_code})'}), 400
            content = img_response.content
            
        else:
            return jsonify({'error': '画像データ(image_base64) または URLが必要です'}), 400

        # --- Vision APIへリクエスト ---
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=content)

        results = []

        if mode == 'label':
            response = client.label_detection(image=image)
            labels = response.label_annotations
            for label in labels:
                results.append({'description': label.description, 'score': f"{label.score:.2%}"})

        elif mode == 'ocr':
            response = client.text_detection(image=image)
            texts = response.text_annotations
            if texts:
                clean_text = texts[0].description.replace('\n', ' ')
                results.append({'description': clean_text, 'score': "N/A"})
            else:
                results.append({'description': "文字なし", 'score': ""})

        elif mode == 'face':
            response = client.face_detection(image=image)
            faces = response.face_annotations
            likelihood_name = ('不明', '極低い', '低い', '中程度', '高い', '極高い')
            if not faces: results.append({'description': "顔なし", 'score': ""})
            for i, face in enumerate(faces):
                results.append({
                    'description': f"顔#{i+1} 笑顔: {likelihood_name[face.joy_likelihood]}",
                    'score': f"確信度: {face.detection_confidence:.2%}"
                })
        
        else:
            return jsonify({'error': '未対応モード'}), 400

        if response.error.message:
            return jsonify({'error': response.error.message}), 500

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

