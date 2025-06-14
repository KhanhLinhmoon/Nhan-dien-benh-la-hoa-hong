import sys
import os
import cv2
import json
import numpy as np
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

# Khởi tạo ứng dụng Flask
app = Flask(__name__, static_url_path='/static', template_folder='.')
CORS(app)

# Đọc file JSON chứa thông tin bệnh
with open('static/solve/solve.json', encoding='utf-8') as json_file:
    solve_data = json.load(json_file)

# Cấu hình YOLOv8
class YoloConfig:
    def __init__(self):
        self.weights = "best2.pt"  # Đường dẫn đến file weights YOLOv8
        self.img_size = (640, 640)
        self.conf_threshold = 0.25
        self.iou_threshold = 0.45
        self.device = 'cpu'  # Có thể đổi thành 'cuda' nếu có GPU
        try:
            print(f"Loading YOLOv8 model from {self.weights}...")
            self.model = YOLO(self.weights)
            self.names = self.model.names
            print("YOLOv8 model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

        # Ánh xạ nhãn tiếng Anh sang tiếng Việt
        self.label_mapping = {
            "black spot": "Đốm đen",
            "downy mildew": "Sương mai",
            "leaf": "Lá khỏe mạnh",
            "mosaic": "Khảm lá",
            "powdery mildew": "Phấn trắng"
        }
        # Màu sắc cho từng class
        self.colors = [
            (0, 255, 0),  # Xanh lá
            (255, 0, 0),  # Đỏ
            (0, 0, 255),  # Xanh dương
            (255, 255, 0),  # Vàng
            (128, 0, 128)  # Tím
        ]

# Khởi tạo cấu hình YOLO
yolo_config = YoloConfig()

def detect_image(image_path):
    """
    Trả về danh sách class_id và đường dẫn ảnh đã xử lý.    Hàm nhận diện ảnh bằng YOLOv8 và vẽ bounding box/nhãn lên ảnh.

    """
    try:
        print(f"Processing image: {image_path}")
        if yolo_config.model is None:
            print("Model not loaded, returning error.")
            return [], None

        # Đọc ảnh bằng OpenCV
        im0 = cv2.imread(image_path)
        if im0 is None:
            print(f"Failed to load image: {image_path}")
            return [], None

        # Thực hiện inference với YOLOv8
        results = yolo_config.model.predict(
            source=im0,
            imgsz=yolo_config.img_size,
            conf=yolo_config.conf_threshold,
            iou=yolo_config.iou_threshold,
            device=yolo_config.device
        )
        print("Inference completed.")

        # Lấy kết quả từ YOLOv8
        class_ids = []
        boxes = results[0].boxes.xyxy.cpu().numpy()  # Tọa độ bounding box
        scores = results[0].boxes.conf.cpu().numpy()  # Độ tin cậy
        classes = results[0].boxes.cls.cpu().numpy()  # ID class

        # Chuyển ảnh sang PIL để vẽ
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
            # Vẽ bounding box
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            # Vẽ nhãn
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except IOError:
                font = ImageFont.load_default()
            text_bbox = draw.textbbox((x1, y1 - 30), label, font=font)
            draw.rectangle(text_bbox, fill=(255, 255, 255))
            draw.text((x1, y1 - 30), label, fill=(0, 0, 0), font=font)

        # Chuyển ảnh từ PIL về OpenCV để lưu
        im0_rgb = np.array(pil_image)
        im0 = cv2.cvtColor(im0_rgb, cv2.COLOR_RGB2BGR)

        # Lưu ảnh kết quả
        output_filename = os.path.basename(image_path).replace(".jpg", "_detected.jpg")
        output_path = os.path.join("static/images", output_filename)
        cv2.imwrite(output_path, im0)
        print(f"Output image saved at: {output_path}")

        return list(set(class_ids)), f"/static/images/{output_filename}"

    except Exception as e:
        print(f"Error during detection: {e}")
        return [], None

@app.route("/")
def index():
    """Route chính để hiển thị giao diện."""
    return render_template("index1.html")

@app.route("/detect", methods=["POST"])
def detect():
    """Route xử lý nhận diện ảnh và trả về kết quả JSON."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    img_file = request.files['file']
    if img_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    img_path = os.path.join("static/images", img_file.filename)
    img_file.save(img_path)

    class_ids, path_detected = detect_image(img_path)
    class_ids = list(set(class_ids))
    result = {}

    for i, class_id in enumerate(class_ids):
        original_label = yolo_config.names[class_id].lower()
        vietnamese_label = yolo_config.label_mapping.get(original_label, original_label)
        result[str(i)] = {
            "name": vietnamese_label,
            "treatment": solve_data.get(str(class_id), {}).get("treatment", "Không xác định"),
            "guide": solve_data.get(str(class_id), {}).get("guide", "Không xác định")
        }
    result["path"] = path_detected
    print("Response JSON:", result)
    return jsonify(result)

@app.route('/favicon.ico')
def favicon():
    """Xử lý yêu cầu favicon."""
    return '', 204

if __name__ == "__main__":
    app.run(debug=True)