from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# 確保上傳資料夾存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return jsonify({"filepath": filepath})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/generate", methods=["POST"])
def generate():
    try:
        # 使用 request.form 來獲取其他資料
        data = request.form.get('data')
        if not data:
            return jsonify({'error': 'No data received'}), 400
        data = json.loads(data)  # 解析為字典

        # 從請求中獲取上傳的圖片
        if 'image' not in request.files:
            return jsonify({'error': 'No image file uploaded'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400

        # 保存圖片到本地
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)
        
        # 使用本地路徑處理圖片
        image = Image.open(image_path).convert("1")  # 轉為二值圖像（黑白）

        # 從請求資料獲取生成精靈的參數
        sprite_width = int(data["spriteWidth"])
        sprite_height = int(data["spriteHeight"])
        room_width = int(data["roomWidth"])
        room_height = int(data["roomHeight"])
        sprites_per_row = image.width // sprite_width

        sprite_data = []
        tile_list = []  # 新增的 tile_list
        valid_sprite_count = 0  # 用來追蹤有效精靈的索引
        unique_sprites = {}  # 用於檢測重複精靈，key 為 binary_data 的 tuple

        for sprite_index in range(room_width * room_height):
            x = (sprite_index % sprites_per_row) * sprite_width
            y = (sprite_index // sprites_per_row) * sprite_height
            sprite_crop = image.crop((x, y, x + sprite_width, y + sprite_height))

            binary_data = [
                1 if sprite_crop.getpixel((px, py)) == 0 else 0
                for py in range(sprite_crop.height)
                for px in range(sprite_crop.width)
            ]

            # 檢查是否為空白精靈（所有像素值均為 0）
            if any(binary_data):
                binary_tuple = tuple(binary_data)  # 將 binary_data 轉為 tuple 以便作為字典的 key

                if binary_tuple not in unique_sprites:
                    # 新的精靈，加入 sprite_data 並記錄
                    valid_sprite_count += 1
                    sprite_name = f"{data['spriteName']}_{valid_sprite_count:02}"
                    unique_sprites[binary_tuple] = sprite_name

                    sprite_data.append({
                        "name": sprite_name,
                        "isAvatar": data["isAvatar"],
                        "isWall": data["isWall"],
                        "isItem": data["isItem"],
                        "isTransparent": data["isTransparent"],
                        "colorIndex": int(data["colorIndex"]),
                        "width": sprite_width,
                        "height": sprite_height,
                        "frameList": [binary_data]
                    })

                # 使用已存在的精靈名稱生成對應的 tileList
                tile_list.append({
                    "spriteName": unique_sprites[binary_tuple],
                    "x": sprite_index % room_width,
                    "y": sprite_index // room_width
                })

        # 生成房間數據
        room_data = {
            "name": data["roomName"],
            "paletteName": data["paletteName"],
            "musicName": data["musicName"],
            "tileList": tile_list,  # 使用過濾後的 tile_list
            "scriptList": {"on-enter": "", "on-exit": ""},
            "width": room_width,
            "height": room_height,
            "spriteWidth": sprite_width,
            "spriteHeight": sprite_height,
            "spriteList": sprite_data  # 使用過濾後的 sprite_data
        }

        return jsonify(room_data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/clear", methods=["POST"])
def clear():
    try:
        # 刪除上傳資料夾中的所有文件
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            os.remove(file_path)
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"清除暫存檔案時發生錯誤：{e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
