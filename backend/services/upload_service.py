import io
import logging
import os
import uuid
import warnings
from typing import Dict, Optional, Tuple
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from ml.preprocessing import IMAGE_SIZE, preprocess_image

logger = logging.getLogger(__name__)

# Enforce a strict 25M pixel limit: treat Pillow's DecompressionBombWarning as an error
# AND explicitly check width * height before decoding pixels.
MAX_IMAGE_PIXELS = 25_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
warnings.simplefilter("error", Image.DecompressionBombWarning)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def is_allowed_filename(filename: str) -> bool:
    """Validate extension on the raw basename so non-ASCII names (e.g. 'गाय.jpg') work."""
    if not filename:
        return False
    base = os.path.basename(filename).strip()
    if "." not in base:
        return False
    ext = base.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_and_save_image(file_storage, upload_folder: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Validate upload (format, 5 MB cap, strict 25M pixel cap), strip EXIF via PIL, and save."""
    if file_storage is None or not file_storage.filename:
        return None, "No image file provided."

    raw_name = os.path.basename(file_storage.filename).strip()
    if not is_allowed_filename(raw_name):
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
            if width * height > MAX_IMAGE_PIXELS:
                return None, (
                    f"Image dimensions ({width}x{height} = {width * height:,} pixels) "
                    f"exceed the {MAX_IMAGE_PIXELS:,} pixel maximum limit."
                )
            img.verify()
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        logger.warning("Rejected invalid image upload '%s': %s", raw_name, exc)
        return None, "Uploaded file is corrupted, exceeds the 25,000,000 pixel limit, or is not a valid image."

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
        logger.warning("Failed to re-encode image '%s': %s", raw_name, exc)
        return None, "Could not decode uploaded image pixels."

    os.makedirs(upload_folder, exist_ok=True)
    raw_stem = os.path.splitext(raw_name)[0]
    safe_stem = secure_filename(raw_stem)[:60] or "image"
    unique_filename = f"{uuid.uuid4().hex[:12]}_{safe_stem}.{out_ext}"
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
        "originalName": raw_name,
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
