import io
import logging
import os
import uuid
from typing import Dict, Optional, Tuple
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from ml.preprocessing import IMAGE_SIZE, preprocess_image

logger = logging.getLogger(__name__)

# Guard against decompression bombs before decoding any uploaded file.
Image.MAX_IMAGE_PIXELS = 25_000_000

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def is_allowed_filename(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_and_save_image(file_storage, upload_folder: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Validate an uploaded image, strip metadata by re-encoding via PIL, and save it."""
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
            img.verify()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
        logger.warning("Rejected invalid image upload '%s': %s", original_name, exc)
        return None, "Uploaded file is corrupted, oversized in pixel dimensions, or not a valid image."

    if img_format not in ALLOWED_PIL_FORMATS:
        return None, "Unsupported image encoding. Please upload a valid JPEG or PNG image."

    # Re-open and re-encode through PIL to strip EXIF/GPS metadata and polyglot payloads.
    try:
        with Image.open(io.BytesIO(file_bytes)) as decoded:
            width, height = decoded.size
            clean_rgb = decoded.convert("RGB")
            out_buf = io.BytesIO()
            if img_format == "PNG":
                clean_rgb.save(out_buf, format="PNG")
                out_ext = "png"
            else:
                clean_rgb.save(out_buf, format="JPEG", quality=92)
                out_ext = "jpg"
            clean_bytes = out_buf.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        logger.warning("Failed to re-encode image '%s': %s", original_name, exc)
        return None, "Could not decode uploaded image pixels."

    os.makedirs(upload_folder, exist_ok=True)
    stem = os.path.splitext(original_name)[0][:60] or "image"
    unique_filename = f"{uuid.uuid4().hex[:12]}_{stem}.{out_ext}"
    saved_path = os.path.join(upload_folder, unique_filename)

    with open(saved_path, "wb") as f:
        f.write(clean_bytes)

    preprocessed_tensor = preprocess_image(
        clean_bytes,
        target_size=IMAGE_SIZE,
        normalization="imagenet",
        expand_dims=True,
    )

    return {
        "filename": unique_filename,
        "originalName": original_name,
        "imagePath": f"/uploads/{unique_filename}",
        "width": width,
        "height": height,
        "format": img_format,
        "sizeKB": round(len(clean_bytes) / 1024, 2),
        "preprocessedShape": list(preprocessed_tensor.shape),
        "normalization": "imagenet mean/std",
    }, None


def delete_uploaded_file(upload_folder: str, image_path: Optional[str]) -> bool:
    """Safely remove a stored upload inside `upload_folder` referenced by `/uploads/<name>`."""
    if not image_path or not isinstance(image_path, str):
        return False
    if not image_path.startswith("/uploads/"):
        return False
    filename = os.path.basename(image_path)
    if not filename:
        return False
    target = os.path.join(upload_folder, filename)
    if os.path.isfile(target):
        try:
            os.remove(target)
            return True
        except OSError as exc:
            logger.warning("Could not delete uploaded file %s: %s", target, exc)
    return False
