import io
import os
import sys
import uuid
from PIL import Image
from werkzeug.utils import secure_filename

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.preprocessing import IMAGE_SIZE, preprocess_image

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def is_allowed_filename(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_and_save_image(file_storage, upload_folder):
    if file_storage is None or not file_storage.filename:
        return None, "No image file provided."

    original_name = secure_filename(file_storage.filename)
    if not is_allowed_filename(original_name):
        return None, "Invalid image format. Only JPG, JPEG, and PNG files are allowed."

    file_bytes = file_storage.read()
    size_bytes = len(file_bytes)

    if size_bytes == 0:
        return None, "Uploaded image file is empty."

    if size_bytes > MAX_FILE_SIZE_BYTES:
        return None, "Image file size exceeds the 5 MB limit."

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img_format = (img.format or "").upper()
            width, height = img.size
            img.verify()
    except Exception:
        return None, "Uploaded file is corrupted or not a valid image."

    if img_format not in ALLOWED_PIL_FORMATS:
        return None, "Unsupported image encoding. Please upload a valid JPEG or PNG image."

    os.makedirs(upload_folder, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex[:12]}_{original_name}"
    saved_path = os.path.join(upload_folder, unique_filename)

    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    preprocessed_tensor = preprocess_image(
        file_bytes,
        target_size=IMAGE_SIZE,
        normalization="mobilenet_v2",
        expand_dims=True,
    )

    return {
        "filename": unique_filename,
        "originalName": original_name,
        "imagePath": f"/uploads/{unique_filename}",
        "width": width,
        "height": height,
        "format": img_format,
        "sizeKB": round(size_bytes / 1024, 2),
        "preprocessedShape": list(preprocessed_tensor.shape),
        "normalization": "mobilenet_v2 ([-1.0, 1.0])"
    }, None
