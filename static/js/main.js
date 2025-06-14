document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const resultContainer = document.getElementById('resultContainer');
    const detectedImage = document.getElementById('detectedImage');
    const resultsList = document.getElementById('resultsList');
    const loadingIndicator = document.getElementById('loadingIndicator');

    uploadBtn.addEventListener('click', function() {
        if (!fileInput.files || fileInput.files.length === 0) {
            alert('Please select an image file first!');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        // Show loading indicator
        loadingIndicator.style.display = 'block';
        resultContainer.style.display = 'none';

        fetch('/detect', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Display results
            detectedImage.src = data.detected_image;
            detectedImage.alt = 'Detected Result';

            // Clear previous results
            resultsList.innerHTML = '';

            // Add new results
            for (const [classId, info] of Object.entries(data.results)) {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.innerHTML = `
                    <h5>${info.name}</h5>
                    <p><strong>Treatment:</strong> ${info.treatment}</p>
                    <p><strong>Guide:</strong> ${info.guide}</p>
                `;
                resultsList.appendChild(li);
            }

            resultContainer.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error: ${error.message}`);
        })
        .finally(() => {
            loadingIndicator.style.display = 'none';
        });
    });

    // Preview selected image
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('imagePreview').src = e.target.result;
                document.getElementById('previewContainer').style.display = 'block';
            };
            reader.readAsDataURL(this.files[0]);
        }
    });
});