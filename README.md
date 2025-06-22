# Hướng dẫn cài đặt 
## 1. Cấu trúc thư mục
plant-disease-detection/  
│  
├── static/                     # Thư mục chứa tài nguyên tĩnh  
│   ├── images/                 # Lưu ảnh gốc và ảnh đã nhận diện  
│   │   ├── example.jpg         # Ảnh upload từ người dùng  
│   │   └── example_detected.jpg # Ảnh sau khi nhận diện (tạo tự động)  
│   │  
│   ├── solve/                  # Thư mục chứa dữ liệu giải pháp xử lý bệnh  
│   │   └── solve.json          # File JSON chứa thông tin cách xử lý từng bệnh  
│   │  
│   └── history.json            # File lưu lịch sử nhận diện (tạo tự động)  
│
├── templates/                  # Thư mục chứa file HTML (dù code hiện tại dùng template_folder  
│   └── index.html             # Giao diện chính của ứng dụng  
│  
├── best13.pt                   # Model YOLOv8 đã trained (từ ultralytics)  
│  
├── app.py                      # File chính chứa toàn bộ code Flask (file bạn đã cung cấp)  

## Cài đặt VS code

## Cài đặt pycharm
Cài đặt các thư viện: numpy, cv2, flask, json, os, ultralytics, datetime.  

Chạy file app.py
