from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
import mysql.connector
import bcrypt

# Tạo Blueprint cho authentication
auth = Blueprint('auth', __name__)

# Cấu hình kết nối MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',  # Thay bằng username MySQL của bạn
    'password': '123456',  # Thay bằng password MySQL của bạn
    'database': 'user_authentication'
}

try:
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    print("Kết nối MySQL trong auth.py thành công!")
except mysql.connector.Error as err:
    print(f"Lỗi kết nối MySQL trong auth.py: {err}")
    exit(1)

# Route đăng ký
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Mật khẩu không khớp!', 'error')
            return render_template('register.html')

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email đã được sử dụng!', 'error')
            return render_template('register.html')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            db.commit()
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
        except mysql.connector.Error as err:
            db.rollback()
            flash(f'Đăng ký thất bại: {err}', 'error')
            return render_template('register.html')

    return render_template('register.html')

# Route đăng nhập
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username']
        password = request.form['password']

        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username = %s OR email = %s",
            (username_or_email, username_or_email)
        )
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['user_id'] = user[0]  # Lưu user_id vào session
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Tên người dùng/email hoặc mật khẩu không đúng!', 'error')
            return render_template('login.html')

    return render_template('login.html')

# Route đăng xuất
@auth.route('/logout')
def logout():
    session.pop('user_id', None)  # Xóa user_id khỏi session
    flash('Đăng xuất thành công!', 'success')
    return redirect(url_for('auth.login'))