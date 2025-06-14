import sys
sys.path.append("D:/project/yolov5")
from flask import Flask, render_template, request
import cv2
import json
import os
from yolov5.models.common import DetectMultiBackend  # ✅ load model chuẩn
from yolov5.utils.general import non_max_suppression
from yolov5.utils.augmentations import letterbox
from yolov5.utils.torch_utils import select_device
import torch
import numpy as np
import pathlib
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
app = Flask(__name__, static_url_path='/static', template_folder='.')  # ✅ nên là '/static' chứ không phải '/project'

# ✅ Đọc file JSON
with open('static/solve/solve.json', encoding='utf-8') as json_file:
    solve = json.load(json_file)
pathlib.PosixPath = pathlib.WindowsPath
class YoloV5:
    def __init__(self, weights = 'best.pt'):
        self.device = select_device('cpu')
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights, force_reload= False)
        self.stride, self.names = self.model.stride, self.model.names
        self.imgsz = (640, 640)
        self.classes = {
            0: "Sau ve bua",
            1: "Phan trang",
            2: "Nam ri sat",
            3: "Dom rong",
            4: "Lá khỏe"
        }
        self.colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (128, 0, 128)]

    def predict(self, path):
        img0 = cv2.imread(path)
        img = letterbox(img0, self.imgsz, stride=self.stride, auto=True)[0]
        img = img.transpose((2, 0, 1))[::-1]  # BGR to RGB, to 3xHxW
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(self.device).float() / 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        pred = self.model(img)
        pred = non_max_suppression(pred, conf_thres=0.25, iou_thres=0.45)[0]
        class_ids = []

        for *xyxy, conf, cls in pred:
            class_id = int(cls.item())
            class_ids.append(class_id)
            x1, y1, x2, y2 = map(int, xyxy)
            label = f"{self.names[class_id]} {conf:.2f}"
            color = self.colors[class_id % len(self.colors)]
            cv2.rectangle(img0, (x1, y1), (x2, y2), color, 2)
            cv2.putText(img0, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        output_path = path.replace(".jpg", "_detected.jpg")
        cv2.imwrite(output_path, img0)
        return class_ids, output_path

model = YoloV5()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect", methods=["POST"])
def detect():
    img_file = request.files['file']
    img_path = os.path.join("static/images", img_file.filename)
    img_file.save(img_path)

    class_ids, path_detected = model.predict(img_path)
    class_ids = list(set(class_ids))
    result = {}

    for i, class_id in enumerate(class_ids):
        result[str(i)] = {
            "name": solve[str(class_id)]["name"],
            "treatment": solve[str(class_id)]["treatment"],
            "guide": solve[str(class_id)]["guide"]
        }
    result["path"] = path_detected
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    app.run(debug=True)
