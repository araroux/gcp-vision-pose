import os
import tkinter as tk
from tkinter import filedialog, messagebox, Radiobutton, IntVar
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
print("Using API_URL =", API_URL)

class VisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GCP Vision AI アプリ (最終版)")
        self.root.geometry("500x650")

        # 変数
        self.file_path = None
        self.mode_var = IntVar(value=0) # 0:Label, 1:OCR, 2:Face

        # --- UI配置 ---
        
        # 1. 画像選択エリア
        self.btn_select = tk.Button(root, text="画像ファイルを選択", command=self.select_image, bg="#f0f0f0")
        self.btn_select.pack(pady=10)

        # 画像プレビュー用ラベル
        self.lbl_preview = tk.Label(root, text="画像が選択されていません", bg="#cccccc", width=50, height=15)
        self.lbl_preview.pack(pady=5)

        # 2. モード選択エリア
        frame_mode = tk.Frame(root)
        frame_mode.pack(pady=10)
        tk.Label(frame_mode, text="AIモード: ").pack(side=tk.LEFT)
        
        modes = [("物体認識(Label)", "label"), ("文字読取(OCR)", "ocr"), ("顔診断(Face)", "face")]
        self.mode_map = ["label", "ocr", "face"] # インデックス対応用
        
        for i, (text, mode_key) in enumerate(modes):
            Radiobutton(frame_mode, text=text, variable=self.mode_var, value=i).pack(side=tk.LEFT, padx=5)

        # 3. 実行ボタン
        self.btn_send = tk.Button(root, text="AI分析開始", command=self.analyze_image, bg="#007acc", fg="white", font=("bold", 12))
        self.btn_send.pack(pady=10, fill=tk.X, padx=50)

        # 4. 結果表示エリア
        self.result_text = tk.Text(root, height=15, width=60)
        self.result_text.pack(pady=10, padx=10)

    def select_image(self):
        # ファイルダイアログを開く
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            self.file_path = file_path
            self.show_preview(file_path)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "画像を選択しました。モードを選んで「AI分析開始」を押してください。")

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

        # 選択されたモードを取得
        selected_mode = self.mode_map[self.mode_var.get()]

        self.btn_send['state'] = 'disabled'
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, f"AIに送信中... (モード: {selected_mode})\n")
        self.root.update()

        try:
            # 画像をBase64に変換
            with open(self.file_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode('utf-8')

            # ペイロード作成
            payload = {
                "image_base64": b64_data,
                "mode": selected_mode
            }

            # 送信
            response = requests.post(API_URL, json=payload, headers=auth_headers())
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert(tk.END, "【判定結果】\n" + "-" * 40 + "\n")
                
                if not results:
                    self.result_text.insert(tk.END, "結果なし（判定できませんでした）\n")
                
                for item in results:
                    desc = item.get('description', '')
                    score = item.get('score', '')
                    self.result_text.insert(tk.END, f"・{desc}  [{score}]\n")
            else:
                self.result_text.insert(tk.END, f"エラー発生: {response.status_code}\n{response.text}")

        except Exception as e:
            messagebox.showerror("エラー", f"通信エラー:\n{str(e)}")
        finally:
            self.btn_send['state'] = 'normal'

if __name__ == "__main__":
    root = tk.Tk()
    app = VisionApp(root)
    root.mainloop()

    