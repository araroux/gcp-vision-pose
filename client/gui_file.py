import os
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import base64
from PIL import Image, ImageTk  # pip install Pillow が必要
from dotenv import load_dotenv
load_dotenv()
from client.auth import auth_headers

API_URL = os.environ.get(
    "VISION_API_URL",
    "http://localhost:8080"
)
DETECT_ENDPOINT = f"{API_URL}/detect"
print("Using API_URL =", API_URL)

class PoseDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pose Landmark Detection")
        self.root.geometry("500x550")

        # 変数
        self.file_path = None

        # --- UI配置 ---

        # 1. 画像選択エリア
        self.btn_select = tk.Button(root, text="画像ファイルを選択", command=self.select_image, bg="#f0f0f0")
        self.btn_select.pack(pady=10)

        # 画像プレビュー用ラベル
        self.lbl_preview = tk.Label(root, text="画像が選択されていません", bg="#cccccc", width=50, height=15)
        self.lbl_preview.pack(pady=5)

        # 2. 実行ボタン
        self.btn_send = tk.Button(root, text="姿勢検出を開始", command=self.analyze_image, bg="#007acc", fg="white", font=("bold", 12))
        self.btn_send.pack(pady=10, fill=tk.X, padx=50)

        # 3. 結果表示エリア
        self.result_text = tk.Text(root, height=15, width=60)
        self.result_text.pack(pady=10, padx=10)

    def select_image(self):
        # ファイルダイアログを開く
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            self.file_path = file_path
            self.show_preview(file_path)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "画像を選択しました。「姿勢検出を開始」を押してください。")

    def show_preview(self, path):
        # 画像をGUIに表示できるサイズにリサイズして表示
        try:
            img = Image.open(path)
            img.thumbnail((300, 300)) # プレビュー用に縮小
            self.photo = ImageTk.PhotoImage(img)
            self.lbl_preview.config(image=self.photo, text="", width=0, height=0) # テキストを消して画像を表示
        except Exception as e:
            self.lbl_preview.config(text=f"プレビューエラー: {e}")

    def analyze_image(self):
        if not self.file_path:
            messagebox.showwarning("警告", "まずは画像を選択してください！")
            return

        self.btn_send['state'] = 'disabled'
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, "APIに送信中...\n")
        self.root.update()

        try:
            # 画像をBase64に変換
            with open(self.file_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode('utf-8')

            # ペイロード作成
            payload = {
                "image_base64": b64_data
            }

            # 送信
            response = requests.post(DETECT_ENDPOINT, json=payload, headers=auth_headers(API_URL))

            if response.status_code == 200:
                data = response.json()
                landmarks = data.get("landmarks", [])
                image_size = data.get("image_size", {})
                inference_ms = data.get("inference_ms", 0)

                self.result_text.delete("1.0", tk.END)
                self.result_text.insert(tk.END, "【検出結果】\n" + "-" * 50 + "\n")
                self.result_text.insert(tk.END, f"画像サイズ: {image_size.get('width')}x{image_size.get('height')}\n")
                self.result_text.insert(tk.END, f"推論時間: {inference_ms}ms\n")
                self.result_text.insert(tk.END, f"ランドマーク数: {len(landmarks)}\n\n")

                if not landmarks:
                    self.result_text.insert(tk.END, "姿勢が検出できませんでした\n")
                else:
                    self.result_text.insert(tk.END, "主要なランドマーク:\n")
                    # Display key landmarks
                    key_landmarks = ["NOSE", "LEFT_SHOULDER", "RIGHT_SHOULDER",
                                   "LEFT_ELBOW", "RIGHT_ELBOW", "LEFT_WRIST", "RIGHT_WRIST",
                                   "LEFT_HIP", "RIGHT_HIP", "LEFT_KNEE", "RIGHT_KNEE"]
                    for lm in landmarks:
                        if lm.get("name") in key_landmarks:
                            name = lm.get("name", "")
                            x = lm.get("x", 0)
                            y = lm.get("y", 0)
                            vis = lm.get("visibility", 0)
                            self.result_text.insert(tk.END, f"  {name}: ({x:.3f}, {y:.3f}) 信頼度:{vis:.2f}\n")
            else:
                self.result_text.insert(tk.END, f"エラー発生: {response.status_code}\n{response.text}")

        except Exception as e:
            messagebox.showerror("エラー", f"通信エラー:\n{str(e)}")
        finally:
            self.btn_send['state'] = 'normal'

if __name__ == "__main__":
    root = tk.Tk()
    app = PoseDetectionApp(root)
    root.mainloop()