import os
from flask import Flask, request, jsonify
from google.cloud import vision

app = Flask(__name__)

@app.route('/', methods=['POST'])
def analyze_image():
    # リクエストから画像URLを取得
    data = request.get_json()
    image_uri = data.get('url')

    if not image_uri:
        return jsonify({'error': 'URLが必要です'}), 400

    try:
        # Vision APIクライアントの初期化
        client = vision.ImageAnnotatorClient()
        image = vision.Image()
        image.source.image_uri = image_uri

        # ラベル検出（物体認識）を実行
        response = client.label_detection(image=image)
        labels = response.label_annotations

        # 結果をリスト化
        results = []
        for label in labels:
            results.append({
                'description': label.description, # 物体の名前
                'score': f"{label.score:.2%}"    # 確信度
            })

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    # ポート設定（Cloud Runの環境変数に合わせる）
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    