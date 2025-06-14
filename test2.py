import sys
import os
import cv2
import json
import numpy as np
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from datetime import datetime

app = Flask(__name__, static_url_path='/static', template_folder='.')
CORS(app)

HISTORY_FILE = 'static/history.json'

try:
    with open('static/solve/solve.json', encoding='utf-8') as json_file:
        solve_data = json.load(json_file)
except FileNotFoundError:
    solve_data = {}
    print("Warning: solve.json not found. Using empty dictionary.")

class YoloConfig:
    def __init__(self):
        self.weights = "best2.pt"
        self.img_size = (640, 640)
        self.conf_threshold = 0.5
        self.iou_threshold = 0.45
        self.device = 'cpu'
        self.model = None
        self.names = []
        try:
            print(f"Loading YOLOv8 model from {self.weights}...")
            self.model = YOLO(self.weights)
            self.names = self.model.names
            print("YOLOv8 model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Model loading failed. Please check the weights file path or install required dependencies.")

        self.label_mapping = {
            "black spot": "Đốm đen",
            "downy mildew": "Sương mai",
            "leaf": "Lá khỏe mạnh",
            "mosaic": "Khảm lá",
            "powdery mildew": "Phấn trắng"
        }
        self.colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (128, 0, 128)]

yolo_config = YoloConfig()

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def detect_image(image_path):
    if yolo_config.model is None:
        print("Model not loaded. Skipping detection.")
        return [], None

    try:
        print(f"Processing image: {image_path}")
        im0 = cv2.imread(image_path)
        if im0 is None:
            print(f"Failed to load image: {image_path}")
            return [], None

        results = yolo_config.model.predict(
            source=im0,
            imgsz=yolo_config.img_size,
            conf=yolo_config.conf_threshold,
            iou=yolo_config.iou_threshold,
            device=yolo_config.device
        )
        print("Inference completed.")

        class_ids = []
        boxes = results[0].boxes.xyxy.cpu().numpy()
        scores = results[0].boxes.conf.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()

        im0_rgb = cv2.cvtColor(im0, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(im0_rgb)
        draw = ImageDraw.Draw(pil_image)

        for box, score, cls in zip(boxes, scores, classes):
            class_id = int(cls)
            class_ids.append(class_id)
            original_label = yolo_config.names[class_id]
            vietnamese_label = yolo_config.label_mapping.get(original_label.lower(), original_label)
            label = f"{vietnamese_label} {score:.2f}"
            x1, y1, x2, y2 = map(int, box)
            color = yolo_config.colors[class_id % len(yolo_config.colors)]
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except IOError:
                font = ImageFont.load_default()
            text_bbox = draw.textbbox((x1, y1 - 30), label, font=font)
            draw.rectangle(text_bbox, fill=(255, 255, 255))
            draw.text((x1, y1 - 30), label, fill=(0, 0, 0), font=font)

        im0_rgb = np.array(pil_image)
        im0 = cv2.cvtColor(im0_rgb, cv2.COLOR_RGB2BGR)

        output_filename = os.path.basename(image_path).replace(".jpg", "_detected.jpg")
        output_path = os.path.join("static/images", output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, im0)
        print(f"Output image saved at: {output_path}")

        return list(set(class_ids)), f"/static/images/{output_filename}"

    except Exception as e:
        print(f"Error during detection: {e}")
        return [], None

@app.route("/")
def index():
    return render_template("index1.html")

@app.route("/detect", methods=["POST"])
def detect():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    img_file = request.files['file']
    if img_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    img_path = os.path.join("static/images", img_file.filename)
    os.makedirs(os.path.dirname(img_path), exist_ok=True)
    img_file.save(img_path)

    class_ids, path_detected = detect_image(img_path)
    class_ids = list(set(class_ids))
    result = {}

    for i, class_id in enumerate(class_ids):
        original_label = yolo_config.names[class_id].lower() if yolo_config.names else "Unknown"
        vietnamese_label = yolo_config.label_mapping.get(original_label, original_label)
        result[str(i)] = {
            "name": vietnamese_label,
            "treatment": solve_data.get(str(class_id), {}).get("treatment", "Không xác định"),
            "guide": solve_data.get(str(class_id), {}).get("guide", "Không xác định")
        }
    result["path"] = path_detected

    if path_detected:
        history = load_history()
        history_entry = {
            "id": len(history),
            "original_image": f"/static/images/{img_file.filename}",
            "detected_image": path_detected,
            "result": ", ".join([f"{result[str(i)]['name']}" for i in range(len(class_ids))]),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "Delete"
        }
        history.append(history_entry)
        save_history(history)

    print("Response JSON:", result)
    return jsonify(result)

@app.route("/history", methods=["GET"])
def get_history():
    history = load_history()
    return jsonify(history)

@app.route("/history/<int:id>", methods=["DELETE"])
def delete_history(id):
    history = load_history()
    if 0 <= id < len(history):
        history.pop(id)
        save_history(history)
        return '', 200
    return jsonify({'error': 'ID không hợp lệ'}), 404

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)