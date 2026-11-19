"""
Day 6: Dataset Organization & Image Preprocessing Pipeline for MobileNetV2.

Provides:
1. Dataset directory initialization (`train/`, `val/`, `test/` across supported classes)
2. Raw dataset splitting (70% train / 15% val / 15% test) and image integrity verification
3. Image loading, RGB conversion, 224x224 resizing, and MobileNetV2 normalization
4. Training data augmentation (horizontal flip, rotation, brightness/contrast, zoom)
5. Sample dataset seeding for local pipeline verification
"""

import argparse
import io
import json
import os
import random
import shutil
import tempfile
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageEnhance

try:
    import cv2  # Optional OpenCV acceleration
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

ML_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATASET_DIR = os.path.join(ML_DIR, "dataset")

SUPPORTED_ANIMALS = ("cow", "buffalo")
CLASS_NAMES = (
    "healthy",
    "lumpy_skin_disease",
    "foot_and_mouth_disease",
)
CLASS_DISPLAY_NAMES = {
    "healthy": "Healthy",
    "lumpy_skin_disease": "Lumpy Skin Disease (LSD)",
    "foot_and_mouth_disease": "Foot-and-Mouth Disease (FMD)",
}
SPLITS = ("train", "val", "test")
DEFAULT_SPLIT_RATIOS = (0.70, 0.15, 0.15)

IMAGE_SIZE: Tuple[int, int] = (224, 224)
IMAGE_SHAPE: Tuple[int, int, int] = (224, 224, 3)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def is_valid_image_file(filepath: str) -> bool:
    """Return True if filepath has an allowed extension and can be decoded as an image."""
    if not os.path.isfile(filepath):
        return False
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    try:
        with Image.open(filepath) as img:
            img.verify()
        return True
    except Exception:
        return False


def load_rgb_image(
    image_source: Union[str, bytes, Image.Image],
    target_size: Tuple[int, int] = IMAGE_SIZE,
) -> Image.Image:
    """
    Load an image from a file path, raw bytes, or PIL Image, convert it to RGB,
    and resize it to `target_size` (224 x 224).
    """
    if isinstance(image_source, Image.Image):
        img = image_source.copy()
    elif isinstance(image_source, (bytes, bytearray)):
        img = Image.open(io.BytesIO(image_source))
    elif isinstance(image_source, str):
        if not os.path.isfile(image_source):
            raise FileNotFoundError(f"Image file not found: {image_source}")
        if HAS_CV2:
            bgr = cv2.imread(image_source)
            if bgr is not None:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                resized = cv2.resize(rgb, target_size, interpolation=cv2.INTER_AREA)
                return Image.fromarray(resized)
        img = Image.open(image_source)
    else:
        raise TypeError("Unsupported image_source type. Expected path, bytes, or PIL.Image.")

    if img.mode != "RGB":
        img = img.convert("RGB")

    resample_filter = getattr(Image, "Resampling", Image).BILINEAR
    img = img.resize(target_size, resample=resample_filter)
    return img


def normalize_pixels(
    image_array: np.ndarray,
    mode: str = "mobilenet_v2",
) -> np.ndarray:
    """
    Normalize a 224x224x3 RGB float32 array.
    - 'mobilenet_v2': scales [0, 255] -> [-1.0, 1.0] via (x / 127.5) - 1.0
    - 'unit': scales [0, 255] -> [0.0, 1.0] via x / 255.0
    """
    arr = image_array.astype(np.float32)
    if mode == "mobilenet_v2":
        return (arr / 127.5) - 1.0
    if mode == "unit":
        return arr / 255.0
    raise ValueError(f"Unsupported normalization mode '{mode}'. Use 'mobilenet_v2' or 'unit'.")


def preprocess_image(
    image_source: Union[str, bytes, Image.Image],
    target_size: Tuple[int, int] = IMAGE_SIZE,
    normalization: str = "mobilenet_v2",
    expand_dims: bool = True,
) -> np.ndarray:
    """
    Full MobileNetV2 preprocessing pipeline for a single image:
    1. Load and convert to 3-channel RGB
    2. Resize to 224 x 224
    3. Convert to float32 NumPy array and normalize pixels
    4. Optionally expand batch dimension to (1, 224, 224, 3)
    """
    pil_img = load_rgb_image(image_source, target_size=target_size)
    rgb_array = np.asarray(pil_img, dtype=np.float32)
    normalized = normalize_pixels(rgb_array, mode=normalization)
    if expand_dims:
        return np.expand_dims(normalized, axis=0)
    return normalized


def augment_image(
    pil_img: Image.Image,
    rng: Optional[random.Random] = None,
) -> Image.Image:
    """
    Apply lightweight data augmentation suitable for livestock disease images:
    - Random horizontal flip (50% chance)
    - Random rotation between -15 and +15 degrees
    - Random brightness and contrast adjustment (0.88 to 1.12)
    - Slight random zoom/crop (90% to 100% area) resized back to 224x224
    """
    rand = rng or random
    img = pil_img.convert("RGB")
    width, height = img.size

    # 1. Horizontal flip
    if rand.random() < 0.5:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    # 2. Slight rotation
    angle = rand.uniform(-15.0, 15.0)
    resample_filter = getattr(Image, "Resampling", Image).BILINEAR
    img = img.rotate(angle, resample=resample_filter, expand=False)

    # 3. Slight random zoom crop
    crop_scale = rand.uniform(0.90, 1.0)
    if crop_scale < 0.99:
        crop_w = int(width * crop_scale)
        crop_h = int(height * crop_scale)
        left = rand.randint(0, max(0, width - crop_w))
        top = rand.randint(0, max(0, height - crop_h))
        img = img.crop((left, top, left + crop_w, top + crop_h))
        img = img.resize((width, height), resample=resample_filter)

    # 4. Brightness and contrast jitter
    brightness_factor = rand.uniform(0.88, 1.12)
    contrast_factor = rand.uniform(0.88, 1.12)
    img = ImageEnhance.Brightness(img).enhance(brightness_factor)
    img = ImageEnhance.Contrast(img).enhance(contrast_factor)

    return img


def resolve_writable_dataset_dir(preferred_dir: str = DEFAULT_DATASET_DIR) -> str:
    """Return preferred_dir if writable; otherwise fall back to a temp directory."""
    try:
        os.makedirs(preferred_dir, exist_ok=True)
        probe_dir = os.path.join(preferred_dir, ".write_probe")
        os.makedirs(probe_dir, exist_ok=True)
        os.rmdir(probe_dir)
        return preferred_dir
    except Exception:
        fallback = os.path.join(tempfile.gettempdir(), "animalcare_dataset")
        os.makedirs(fallback, exist_ok=True)
        return fallback


def init_dataset_directories(dataset_root: str = DEFAULT_DATASET_DIR) -> Dict[str, List[str]]:
    """
    Create standard train/val/test class subdirectories under `ml/dataset/`:
      ml/dataset/
        raw/
          healthy/
          lumpy_skin_disease/
          foot_and_mouth_disease/
        train/
          healthy/
          lumpy_skin_disease/
          foot_and_mouth_disease/
        val/
          ...
        test/
          ...
    """
    dataset_root = resolve_writable_dataset_dir(dataset_root)
    created_paths: List[str] = []
    for folder in ("raw",) + SPLITS:
        for class_name in CLASS_NAMES:
            dir_path = os.path.join(dataset_root, folder, class_name)
            os.makedirs(dir_path, exist_ok=True)
            created_paths.append(dir_path)

    metadata_path = os.path.join(dataset_root, "class_indices.json")
    class_mapping = {name: idx for idx, name in enumerate(CLASS_NAMES)}
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "class_indices": class_mapping,
                "class_display_names": CLASS_DISPLAY_NAMES,
                "supported_animals": list(SUPPORTED_ANIMALS),
                "image_size": list(IMAGE_SIZE),
                "normalization": "mobilenet_v2 ([-1.0, 1.0])",
            },
            f,
            indent=2,
        )

    return {
        "dataset_root": dataset_root,
        "directories": created_paths,
        "metadata_file": metadata_path,
    }


def organize_raw_dataset(
    raw_dir: Optional[str] = None,
    dataset_root: str = DEFAULT_DATASET_DIR,
    split_ratios: Tuple[float, float, float] = DEFAULT_SPLIT_RATIOS,
    seed: int = 42,
) -> Dict[str, Dict[str, int]]:
    """
    Validate images in `raw/<class_name>/`, resize to 224x224 RGB, and split them
    into `train/`, `val/`, and `test/` according to `split_ratios` (70/15/15).
    """
    info = init_dataset_directories(dataset_root)
    dataset_root = info["dataset_root"]
    source_root = raw_dir or os.path.join(dataset_root, "raw")
    rng = random.Random(seed)

    summary: Dict[str, Dict[str, int]] = {split: {c: 0 for c in CLASS_NAMES} for split in SPLITS}

    for class_name in CLASS_NAMES:
        class_raw_dir = os.path.join(source_root, class_name)
        if not os.path.isdir(class_raw_dir):
            continue

        valid_files = [
            os.path.join(class_raw_dir, fname)
            for fname in sorted(os.listdir(class_raw_dir))
            if is_valid_image_file(os.path.join(class_raw_dir, fname))
        ]
        if not valid_files:
            continue

        rng.shuffle(valid_files)
        total = len(valid_files)
        train_end = int(round(total * split_ratios[0]))
        val_end = train_end + int(round(total * split_ratios[1]))

        split_assignments = {
            "train": valid_files[:train_end],
            "val": valid_files[train_end:val_end],
            "test": valid_files[val_end:],
        }

        for split_name, file_list in split_assignments.items():
            target_dir = os.path.join(dataset_root, split_name, class_name)
            os.makedirs(target_dir, exist_ok=True)
            for idx, src_path in enumerate(file_list):
                try:
                    img = load_rgb_image(src_path, target_size=IMAGE_SIZE)
                    out_name = f"{class_name}_{split_name}_{idx + 1:04d}.jpg"
                    out_path = os.path.join(target_dir, out_name)
                    img.save(out_path, format="JPEG", quality=92)
                    summary[split_name][class_name] += 1
                except Exception:
                    continue

    return summary


def seed_sample_dataset(
    dataset_root: str = DEFAULT_DATASET_DIR,
    raw_samples_per_class: int = 12,
    seed: int = 42,
) -> Dict[str, Dict[str, int]]:
    """
    Generate synthetic 224x224 RGB sample images in `ml/dataset/raw/` for each class
    ('healthy', 'lumpy_skin_disease', 'foot_and_mouth_disease') and organize them
    into `train/`, `val/`, and `test/` splits so the preprocessing and training
    pipeline can be tested immediately.
    """
    info = init_dataset_directories(dataset_root)
    dataset_root = info["dataset_root"]
    np_rng = np.random.default_rng(seed)

    class_palettes = {
        "healthy": (90, 155, 85),               # Smooth healthy pasture/coat tone
        "lumpy_skin_disease": (165, 110, 80),   # Textured nodular skin pattern
        "foot_and_mouth_disease": (180, 95, 95) # Reddish lesion/blister pattern
    }

    raw_root = os.path.join(dataset_root, "raw")
    for class_name, base_rgb in class_palettes.items():
        class_dir = os.path.join(raw_root, class_name)
        os.makedirs(class_dir, exist_ok=True)

        for i in range(raw_samples_per_class):
            canvas = np.zeros((IMAGE_SIZE[1], IMAGE_SIZE[0], 3), dtype=np.float32)
            for c in range(3):
                jitter = np_rng.uniform(-18, 18)
                noise = np_rng.normal(0, 12, size=(IMAGE_SIZE[1], IMAGE_SIZE[0]))
                canvas[:, :, c] = np.clip(base_rgb[c] + jitter + noise, 0, 255)

            # Add distinct visual patterns per class
            if class_name == "lumpy_skin_disease":
                # Circular nodule-like spots
                for _ in range(8):
                    cx = int(np_rng.integers(25, 200))
                    cy = int(np_rng.integers(25, 200))
                    radius = int(np_rng.integers(6, 14))
                    yy, xx = np.ogrid[:IMAGE_SIZE[1], :IMAGE_SIZE[0]]
                    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
                    canvas[mask] = np.clip(canvas[mask] * 0.65, 0, 255)
            elif class_name == "foot_and_mouth_disease":
                # Bright blister-like horizontal bands/patches
                for _ in range(5):
                    x0 = int(np_rng.integers(20, 160))
                    y0 = int(np_rng.integers(20, 180))
                    w = int(np_rng.integers(18, 40))
                    h = int(np_rng.integers(10, 22))
                    canvas[y0:y0 + h, x0:x0 + w, 0] = 235
                    canvas[y0:y0 + h, x0:x0 + w, 1] = 110
                    canvas[y0:y0 + h, x0:x0 + w, 2] = 110

            pil_img = Image.fromarray(canvas.astype(np.uint8), mode="RGB")
            sample_path = os.path.join(class_dir, f"sample_{class_name}_{i + 1:03d}.jpg")
            pil_img.save(sample_path, format="JPEG", quality=92)

    return organize_raw_dataset(raw_dir=raw_root, dataset_root=dataset_root, seed=seed)


def verify_dataset_structure(dataset_root: str = DEFAULT_DATASET_DIR) -> Dict[str, object]:
    """
    Inspect `ml/dataset/` splits and classes, verify image readability, and return
    counts per split and class.
    """
    if not os.path.isdir(os.path.join(dataset_root, "train")):
        dataset_root = resolve_writable_dataset_dir(dataset_root)
    counts: Dict[str, Dict[str, int]] = {}
    total_valid = 0
    corrupted_files: List[str] = []

    for split_name in SPLITS:
        counts[split_name] = {}
        for class_name in CLASS_NAMES:
            dir_path = os.path.join(dataset_root, split_name, class_name)
            valid_count = 0
            if os.path.isdir(dir_path):
                for fname in os.listdir(dir_path):
                    fpath = os.path.join(dir_path, fname)
                    if not os.path.isfile(fpath):
                        continue
                    if is_valid_image_file(fpath):
                        valid_count += 1
                    else:
                        corrupted_files.append(fpath)
            counts[split_name][class_name] = valid_count
            total_valid += valid_count

    return {
        "dataset_root": dataset_root,
        "image_size": list(IMAGE_SIZE),
        "classes": list(CLASS_NAMES),
        "splits": counts,
        "total_images": total_valid,
        "corrupted_files": corrupted_files,
        "ready_for_training": total_valid > 0 and len(corrupted_files) == 0,
    }


def load_split_arrays(
    split_name: str = "train",
    dataset_root: str = DEFAULT_DATASET_DIR,
    normalization: str = "mobilenet_v2",
    augment: bool = False,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load all images in a split ('train', 'val', or 'test') into preprocessed NumPy
    arrays (X, y, class_names) ready for MobileNetV2 training or evaluation.
    """
    if split_name not in SPLITS:
        raise ValueError(f"Invalid split '{split_name}'. Expected one of {SPLITS}.")
    if not os.path.isdir(os.path.join(dataset_root, split_name)):
        dataset_root = resolve_writable_dataset_dir(dataset_root)

    rng = random.Random(seed)
    images: List[np.ndarray] = []
    labels: List[int] = []

    for class_idx, class_name in enumerate(CLASS_NAMES):
        class_dir = os.path.join(dataset_root, split_name, class_name)
        if not os.path.isdir(class_dir):
            continue
        for fname in sorted(os.listdir(class_dir)):
            fpath = os.path.join(class_dir, fname)
            if not is_valid_image_file(fpath):
                continue
            pil_img = load_rgb_image(fpath, target_size=IMAGE_SIZE)
            if augment:
                pil_img = augment_image(pil_img, rng=rng)
            arr = preprocess_image(
                pil_img,
                target_size=IMAGE_SIZE,
                normalization=normalization,
                expand_dims=False,
            )
            images.append(arr)
            labels.append(class_idx)

    if not images:
        return (
            np.empty((0, IMAGE_SIZE[1], IMAGE_SIZE[0], 3), dtype=np.float32),
            np.empty((0,), dtype=np.int64),
            list(CLASS_NAMES),
        )

    X = np.stack(images, axis=0).astype(np.float32)
    y = np.array(labels, dtype=np.int64)
    return X, y, list(CLASS_NAMES)


def main():
    parser = argparse.ArgumentParser(
        description="Day 6: AnimalCare AI Dataset Organization & MobileNetV2 Preprocessing"
    )
    parser.add_argument(
        "--dataset-dir",
        default=DEFAULT_DATASET_DIR,
        help="Path to the ml/dataset directory",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize raw/, train/, val/, and test/ class folders",
    )
    parser.add_argument(
        "--seed-samples",
        action="store_true",
        help="Generate sample synthetic images and split into train/val/test",
    )
    parser.add_argument(
        "--organize",
        action="store_true",
        help="Organize images from raw/ into train/val/test splits",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify dataset folder structure and image counts",
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Test single-image preprocessing on a file path",
    )
    args = parser.parse_args()

    if args.init:
        info = init_dataset_directories(args.dataset_dir)
        print(f"Initialized {len(info['directories'])} dataset directories under {info['dataset_root']}.")

    if args.seed_samples:
        split_counts = seed_sample_dataset(args.dataset_dir)
        print("Seeded sample dataset and organized splits:")
        print(json.dumps(split_counts, indent=2))

    if args.organize:
        split_counts = organize_raw_dataset(dataset_root=args.dataset_dir)
        print("Organized raw dataset into splits:")
        print(json.dumps(split_counts, indent=2))

    if args.image:
        batch = preprocess_image(args.image, expand_dims=True)
        print(
            f"Preprocessed '{args.image}' -> shape={batch.shape}, dtype={batch.dtype}, "
            f"min={batch.min():.3f}, max={batch.max():.3f}"
        )

    if args.verify or not (args.init or args.seed_samples or args.organize or args.image):
        report = verify_dataset_structure(args.dataset_dir)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
