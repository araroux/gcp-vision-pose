import tkinter as tk
from tkinter import messagebox
import requests

# ==========================================
# ここに Cloud Run の URL を貼り付けてください
# ==========================================
API_URL = "https://my-vision-service-593396693760.asia-northeast1.run.app"

def analyze_image():
    # 1. 入力された画像URLを取得
    target_image_url = entry_url.get()
    
    if not target_image_url:
        messagebox.showwarning("警告", "画像のURLを入力してください！")
        return

    # ボタンを無効化（連打防止）
    btn_send['state'] = 'disabled'
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, "AIが考え中...\n")
    root.update()

    try:
        # 2. クラウド(Cloud Run)にデータを送信
        payload = {"url": target_image_url}
        response = requests.post(API_URL, json=payload)
        
        # 3. 結果を受け取る
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            # 画面に表示
            result_text.delete("1.0", tk.END)
            result_text.insert(tk.END, "【判定結果】\n")
            result_text.insert(tk.END, "-" * 30 + "\n")
            
            for item in results:
                # 猫: 99.5% のように表示
                line = f"{item['description']}: {item['score']}\n"
                result_text.insert(tk.END, line)
        else:
            result_text.insert(tk.END, f"エラーが発生しました: {response.status_code}")

    except Exception as e:
        messagebox.showerror("エラー", f"通信エラー:\n{str(e)}")
    
    finally:
        # ボタンを再度有効にする
        btn_send['state'] = 'normal'

# --- 画面（GUI）を作る ---
root = tk.Tk()
root.title("AI画像判定アプリ")
root.geometry("400x400")

# ラベル
label = tk.Label(root, text="判定したい画像のURLを入力:")
label.pack(pady=10)

# 入力欄
entry_url = tk.Entry(root, width=50)
entry_url.pack(pady=5)
# テスト用に猫のURLを最初から入れておく
entry_url.insert(0, "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg")

# 送信ボタン
btn_send = tk.Button(root, text="AIに判定させる", command=analyze_image, bg="#dddddd", font=("bold", 12))
btn_send.pack(pady=10)

# 結果表示エリア
result_text = tk.Text(root, height=15, width=45)
result_text.pack(pady=10)

# アプリ起動
root.mainloop()
