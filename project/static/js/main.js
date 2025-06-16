function showSection(sectionId, event) {
    event.preventDefault(); // Ngăn chặn hành vi mặc định của liên kết
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');
    const titles = {
        'detect-section': 'PHÁT HIỆN BỆNH TRÊN LÁ HOA HỒNG',
        'history-section': 'LỊCH SỬ NHẬN DIỆN BỆNH',
        'handbook-section': 'SỔ TAY NHẬN DIỆN BỆNH'
    };
    document.getElementById('section-title').textContent = titles[sectionId];
    if (sectionId === 'history-section') {
        loadHistory();
    }
}

function readPath(event) {
    const reader = new FileReader();
    reader.onload = function (e) {
        document.getElementById('input').src = e.target.result;
    };
    reader.readAsDataURL(event.target.files[0]);
}

function sendImage() {
    const fileInput = document.getElementById('img');
    const file = fileInput.files[0];
    if (!file) {
        alert("Vui lòng chọn ảnh.");
        return;
    }

    const formData = new FormData(document.getElementById('detectForm'));
    fetch('/detect', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert("Lỗi: " + data.error);
            return;
        }
        if (!data.path) {
            alert("Không thể xử lý ảnh. Vui lòng kiểm tra mô hình.");
            document.getElementById('output').src = 'static/images/img-500x500.jpg';
        } else {
            document.getElementById('output').src = data.path;
        }

        const tableContainer = document.getElementById('table-container');
        const tbody = document.getElementById('table-body');
        tbody.innerHTML = '';
        let index = 0;
        for (const key in data) {
            if (key !== 'path') {
                const info = data[key];
                const name = info.name || 'Không xác định';
                const row = `
                    <tr>
                        <td class="text-center">${index++}</td>
                        <td>${name}</td>
                        <td>${info.treatment || 'Không xác định'}</td>
                        <td>${info.guide || 'Không xác định'}</td>
                    </tr>`;
                tbody.innerHTML += row;
            }
        }
        tableContainer.style.display = 'block';
    })
    .catch(err => {
        console.error('Lỗi fetch:', err);
        alert("Có lỗi xảy ra khi xử lý ảnh. Kiểm tra console để biết thêm chi tiết.");
    });
}

function loadHistory() {
    fetch('/history')
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('history-body');
            tbody.innerHTML = '';
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Không có dữ liệu lịch sử.</td></tr>';
                return;
            }
            data.forEach((item, index) => {
                const row = `
                    <tr>
                        <td>${index}</td>
                        <td><img src="${item.original_image}" class="history-img"></td>
                        <td><img src="${item.detected_image}" class="history-img"></td>
                        <td>${item.result}</td>
                        <td>${item.date}</td>
                        <td><button class="btn btn-danger btn-sm" onclick="deleteHistory(${item.id})">Xóa</button></td>
                    </tr>`;
                tbody.innerHTML += row;
            });
        })
        .catch(err => {
            console.error('Lỗi tải lịch sử:', err);
            document.getElementById('history-body').innerHTML = '<tr><td colspan="6" class="text-center">Lỗi khi tải lịch sử.</td></tr>';
        });
}

function deleteHistory(id) {
    fetch(`/history/${id}`, { method: 'DELETE' })
        .then(res => {
            if (res.ok) loadHistory();
            else alert('Lỗi khi xóa lịch sử.');
        })
        .catch(err => console.error('Lỗi xóa lịch sử:', err));
}

window.addEventListener('load', () => {
    showSection('detect-section', { preventDefault: () => {} }); // Mặc định hiển thị section "Phát hiện bệnh"
});