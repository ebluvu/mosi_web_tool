from flask import Flask, render_template, request, jsonify
from PIL import Image
import json
import os

app = Flask(__name__)

# 上傳檔案的路徑
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')  # 顯示前端的 HTML 頁面

@app.route('/upload', methods=['POST'])
def upload_file():
    # 接收圖片與參數
    file = request.files['image']
    sprite_width = int(request.form['sprite_width'])
    sprite_height = int(request.form['sprite_height'])
    room_width = int(request.form['room_width'])
    room_height = int(request.form['room_height'])

    # 儲存圖片
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # 執行 Python 圖片處理邏輯
    image = Image.open(file_path)
    image = image.convert("1")  # 黑白二值化

    # 生成數據邏輯（與你的程式類似）
    sprite_data = []
    for sprite_index in range(room_width * room_height):
        x = (sprite_index % (image.width // sprite_width)) * sprite_width
        y = (sprite_index // (image.width // sprite_width)) * sprite_height
        sprite_crop = image.crop((x, y, x + sprite_width, y + sprite_height))
        binary_data = [
            1 if sprite_crop.getpixel((px, py)) == 0 else 0
            for py in range(sprite_height)
            for px in range(sprite_width)
        ]
        sprite_data.append({
            "name": f"rest_{sprite_index + 1}",
            "isAvatar": False,
            "isWall": True,
            "isItem": False,
            "isTransparent": True,
            "colorIndex": 1,
            "width": sprite_width,
            "height": sprite_height,
            "frameList": [binary_data]
        })

    # 房間數據
    room_data = {
        "name": "rest",
        "paletteName": "palette-1",
        "musicName": "song-1",
        "tileList": [],
        "scriptList": {"on-enter": "", "on-exit": ""},
        "width": room_width,
        "height": room_height,
        "spriteWidth": sprite_width,
        "spriteHeight": sprite_height,
        "spriteList": sprite_data
    }
    for y in range(room_data["height"]):
        for x in range(room_data["width"]):
            sprite_index = y * room_data["width"] + x
            room_data["tileList"].append({
                "spriteName": f"rest_{sprite_index + 1}",
                "x": x,
                "y": y
            })

    # 回傳 JSON 結果
    return jsonify(room_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render 使用環境變數 PORT 指定埠號
    app.run(host="0.0.0.0", port=port)       # 綁定到 0.0.0.0
