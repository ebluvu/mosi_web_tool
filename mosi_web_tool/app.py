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
        for sprite_index in range(room_width * room_height):
            x = (sprite_index % sprites_per_row) * sprite_width
            y = (sprite_index // sprites_per_row) * sprite_height
            sprite_crop = image.crop((x, y, x + sprite_width, y + sprite_height))

            binary_data = [
                1 if sprite_crop.getpixel((px, py)) == 0 else 0
                for py in range(sprite_crop.height)
                for px in range(sprite_crop.width)
            ]

            sprite_data.append({
                "name": f"{data['spriteName']}_{sprite_index + 1}",
                "isAvatar": data["isAvatar"],
                "isWall": data["isWall"],
                "isItem": data["isItem"],
                "isTransparent": data["isTransparent"],
                "colorIndex": int(data["colorIndex"]),
                "width": sprite_width,
                "height": sprite_height,
                "frameList": [binary_data]
            })

        # 生成房間數據
        room_data = {
            "name": data["roomName"],
            "paletteName": data["paletteName"],
            "musicName": data["musicName"],
            "tileList": [],
            "scriptList": {"on-enter": "", "on-exit": ""},
            "width": room_width,
            "height": room_height,
            "spriteWidth": sprite_width,
            "spriteHeight": sprite_height,
            "spriteList": sprite_data
        }

        # 自動生成 tileList
        for y in range(room_data["height"]):
            for x in range(room_data["width"]):
                sprite_index = y * room_data["width"] + x
                room_data["tileList"].append({
                    "spriteName": f"{data['spriteName']}_{sprite_index + 1}",
                    "x": x,
                    "y": y
                })

        return jsonify(room_data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
