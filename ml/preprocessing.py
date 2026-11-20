"""
Dataset organisation and image preprocessing for the MobileNetV2 classifier.

IMPORTANT: `seed_sample_dataset()` generates *synthetic* coloured-noise images.
They only exist to exercise the pipeline end to end. A model trained on them
learns colour patterns, not disease, and its accuracy says nothing about real
animals. To train on real data, put labelled photos in
`ml/dataset/raw/<class_name>/` and run `python -m ml.preprocessing --organize`.

Run from the project root, for example:
    python -m ml.preprocessing --init --seed-samples --verify
"""

import argparse
import io
import json
import logging
import os
import random
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageEnhance, UnidentifiedImageError

logger = logging.getLogger(__name__)

ML_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATASET_DIR = os.path.join(ML_DIR, "dataset")
DATASET_SOURCE_FILE = "dataset_source.json"
SYNTHETIC_RAW_DIR = "raw_synthetic"

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

# torchvision's ImageNet weights expect [0, 1] inputs standardised with these values.
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

_IMAGE_ERRORS = (UnidentifiedImageError, OSError, SyntaxError, ValueError)
_RESAMPLE = getattr(Image, "Resampling", Image).BILINEAR


def is_valid_image_file(filepath: str) -> bool:
    """Return True if filepath has an allowed extension and decodes as an image."""
    if not os.path.isfile(filepath):
        return False
    if os.path.splitext(filepath)[1].lower() not in ALLOWED_EXTENSIONS:
        return False
    try:
        with Image.open(filepath) as img:
            img.verify()
        return True
    except _IMAGE_ERRORS as exc:
        logger.warning("Skipping unreadable image %s: %s", filepath, exc)
        return False


def load_rgb_image(
    image_source: Union[str, os.PathLike, bytes, Image.Image],
    target_size: Tuple[int, int] = IMAGE_SIZE,
) -> Image.Image:
    """Load an image (path, bytes or PIL image), convert to RGB and resize it.

    The same PIL bilinear resize is used for every input type so training and
    inference see identical preprocessing. Files are closed immediately.
    """
    if isinstance(image_source, Image.Image):
        img = image_source.convert("RGB")
    elif isinstance(image_source, (bytes, bytearray)):
        with Image.open(io.BytesIO(image_source)) as raw:
            img = raw.convert("RGB")
    elif isinstance(image_source, (str, os.PathLike)):
        with Image.open(image_source) as raw:
            img = raw.convert("RGB")
    else:
        raise TypeError("Unsupported image_source type. Expected path, bytes, or PIL.Image.")
    return img.resize(target_size, resample=_RESAMPLE)


def normalize_pixels(image_array: np.ndarray, mode: str = "imagenet") -> np.ndarray:
    """Normalise an HxWx3 RGB array with values in [0, 255].

    - 'imagenet': x / 255, then standardised with ImageNet mean/std (torchvision convention)
    - 'unit': x / 255
    """
    arr = image_array.astype(np.float32) / 255.0
    if mode == "imagenet":
        return (arr - IMAGENET_MEAN) / IMAGENET_STD
    if mode == "unit":
        return arr
    raise ValueError(f"Unsupported normalization mode '{mode}'. Use 'imagenet' or 'unit'.")


def preprocess_image(
    image_source: Union[str, os.PathLike, bytes, Image.Image],
    target_size: Tuple[int, int] = IMAGE_SIZE,
    normalization: str = "imagenet",
    expand_dims: bool = True,
) -> np.ndarray:
    """Load, resize and normalise one image. Returns (1, 224, 224, 3) by default."""
    pil_img = load_rgb_image(image_source, target_size=target_size)
    normalized = normalize_pixels(np.asarray(pil_img, dtype=np.float32), mode=normalization)
    return np.expand_dims(normalized, axis=0) if expand_dims else normalized


def augment_image(pil_img: Image.Image, rng: Optional[random.Random] = None) -> Image.Image:
    """Light augmentation: flip, +-15 degree rotation, small zoom, brightness/contrast jitter."""
    rand = rng or random
    img = pil_img.convert("RGB")
    width, height = img.size

    if rand.random() < 0.5:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    img = img.rotate(rand.uniform(-15.0, 15.0), resample=_RESAMPLE, expand=False)

    crop_scale = rand.uniform(0.90, 1.0)
    if crop_scale < 0.99:
        crop_w, crop_h = int(width * crop_scale), int(height * crop_scale)
        left = rand.randint(0, max(0, width - crop_w))
        top = rand.randint(0, max(0, height - crop_h))
        img = img.crop((left, top, left + crop_w, top + crop_h)).resize((width, height), resample=_RESAMPLE)

    img = ImageEnhance.Brightness(img).enhance(rand.uniform(0.88, 1.12))
    img = ImageEnhance.Contrast(img).enhance(rand.uniform(0.88, 1.12))
    return img


def _write_dataset_source(dataset_root: str, source: str) -> None:
    with open(os.path.join(dataset_root, DATASET_SOURCE_FILE), "w", encoding="utf-8") as f:
        json.dump({"source": source}, f, indent=2)


def read_dataset_source(dataset_root: str = DEFAULT_DATASET_DIR) -> Dict[str, str]:
    """Return {'source': 'synthetic' | 'user_provided' | 'unknown'} for the current splits."""
    path = os.path.join(dataset_root, DATASET_SOURCE_FILE)
    if not os.path.isfile(path):
        return {"source": "unknown"}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) and "source" in data else {"source": "unknown"}
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read %s: %s", path, exc)
        return {"source": "unknown"}


def init_dataset_directories(dataset_root: str = DEFAULT_DATASET_DIR) -> Dict[str, object]:
    """Create raw/, train/, val/ and test/ class folders plus class_indices.json."""
    created_paths: List[str] = []
    for folder in ("raw",) + SPLITS:
        for class_name in CLASS_NAMES:
            dir_path = os.path.join(dataset_root, folder, class_name)
            os.makedirs(dir_path, exist_ok=True)
            created_paths.append(dir_path)

    metadata_path = os.path.join(dataset_root, "class_indices.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "class_indices": {name: idx for idx, name in enumerate(CLASS_NAMES)},
                "class_display_names": CLASS_DISPLAY_NAMES,
                "supported_animals": list(SUPPORTED_ANIMALS),
                "image_size": list(IMAGE_SIZE),
                "normalization": "imagenet mean/std",
            },
            f,
            indent=2,
        )
    return {"dataset_root": dataset_root, "directories": created_paths, "metadata_file": metadata_path}


def _clear_split_dirs(dataset_root: str) -> None:
    """Remove previously generated split images so old and new data never mix."""
    for split_name in SPLITS:
        for class_name in CLASS_NAMES:
            dir_path = os.path.join(dataset_root, split_name, class_name)
            if not os.path.isdir(dir_path):
                continue
            for fname in os.listdir(dir_path):
                fpath = os.path.join(dir_path, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)


def organize_raw_dataset(
    raw_dir: Optional[str] = None,
    dataset_root: str = DEFAULT_DATASET_DIR,
    split_ratios: Tuple[float, float, float] = DEFAULT_SPLIT_RATIOS,
    seed: int = 42,
    source: str = "user_provided",
) -> Dict[str, Dict[str, int]]:
    """Validate images in raw/<class>/, resize to 224x224 RGB and split 70/15/15."""
    init_dataset_directories(dataset_root)
    _clear_split_dirs(dataset_root)
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
        rng.shuffle(valid_files)
        total = len(valid_files)
        train_end = int(round(total * split_ratios[0]))
        val_end = train_end + int(round(total * split_ratios[1]))
        assignments = {
            "train": valid_files[:train_end],
            "val": valid_files[train_end:val_end],
            "test": valid_files[val_end:],
        }
        for split_name, file_list in assignments.items():
            target_dir = os.path.join(dataset_root, split_name, class_name)
            for idx, src_path in enumerate(file_list):
                try:
                    img = load_rgb_image(src_path, target_size=IMAGE_SIZE)
                    img.save(os.path.join(target_dir, f"{class_name}_{split_name}_{idx + 1:04d}.jpg"), format="JPEG", quality=92)
                    summary[split_name][class_name] += 1
                except _IMAGE_ERRORS as exc:
                    logger.warning("Could not process %s: %s", src_path, exc)

    _write_dataset_source(dataset_root, source)
    return summary


def seed_sample_dataset(
    dataset_root: str = DEFAULT_DATASET_DIR,
    raw_samples_per_class: int = 12,
    seed: int = 42,
) -> Dict[str, Dict[str, int]]:
    """Generate SYNTHETIC placeholder images and split them into train/val/test.

    Each class is a flat colour with noise ('healthy' green, 'lsd' brown with dark
    circles, 'fmd' red with pink rectangles). They are not animal photos. The
    splits are marked as synthetic so training and the API can report it.
    """
    init_dataset_directories(dataset_root)
    np_rng = np.random.default_rng(seed)
    palettes = {
        "healthy": (90, 155, 85),
        "lumpy_skin_disease": (165, 110, 80),
        "foot_and_mouth_disease": (180, 95, 95),
    }
    synthetic_root = os.path.join(dataset_root, SYNTHETIC_RAW_DIR)
    height, width = IMAGE_SIZE[1], IMAGE_SIZE[0]

    for class_name, base_rgb in palettes.items():
        class_dir = os.path.join(synthetic_root, class_name)
        os.makedirs(class_dir, exist_ok=True)
        for i in range(raw_samples_per_class):
            canvas = np.zeros((height, width, 3), dtype=np.float32)
            for c in range(3):
                noise = np_rng.normal(0, 12, size=(height, width))
                canvas[:, :, c] = np.clip(base_rgb[c] + np_rng.uniform(-18, 18) + noise, 0, 255)
            if class_name == "lumpy_skin_disease":
                yy, xx = np.ogrid[:height, :width]
                for _ in range(8):
                    cx, cy = int(np_rng.integers(25, 200)), int(np_rng.integers(25, 200))
                    radius = int(np_rng.integers(6, 14))
                    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
                    canvas[mask] = np.clip(canvas[mask] * 0.65, 0, 255)
            elif class_name == "foot_and_mouth_disease":
                for _ in range(5):
                    x0, y0 = int(np_rng.integers(20, 160)), int(np_rng.integers(20, 180))
                    w, h = int(np_rng.integers(18, 40)), int(np_rng.integers(10, 22))
                    canvas[y0:y0 + h, x0:x0 + w] = (235, 110, 110)
            Image.fromarray(canvas.astype(np.uint8)).save(
                os.path.join(class_dir, f"synthetic_{class_name}_{i + 1:03d}.jpg"), format="JPEG", quality=92
            )

    return organize_raw_dataset(raw_dir=synthetic_root, dataset_root=dataset_root, seed=seed, source="synthetic")


def verify_dataset_structure(dataset_root: str = DEFAULT_DATASET_DIR) -> Dict[str, object]:
    """Count readable images per split/class and report the data source."""
    counts: Dict[str, Dict[str, int]] = {}
    total_valid = 0
    corrupted: List[str] = []
    for split_name in SPLITS:
        counts[split_name] = {}
        for class_name in CLASS_NAMES:
            dir_path = os.path.join(dataset_root, split_name, class_name)
            valid = 0
            if os.path.isdir(dir_path):
                for fname in os.listdir(dir_path):
                    fpath = os.path.join(dir_path, fname)
                    if not os.path.isfile(fpath):
                        continue
                    if is_valid_image_file(fpath):
                        valid += 1
                    else:
                        corrupted.append(fpath)
            counts[split_name][class_name] = valid
            total_valid += valid
    return {
        "dataset_root": dataset_root,
        "data_source": read_dataset_source(dataset_root)["source"],
        "image_size": list(IMAGE_SIZE),
        "classes": list(CLASS_NAMES),
        "splits": counts,
        "total_images": total_valid,
        "corrupted_files": corrupted,
        "ready_for_training": total_valid > 0 and not corrupted,
    }


def load_split_arrays(
    split_name: str = "train",
    dataset_root: str = DEFAULT_DATASET_DIR,
    normalization: str = "imagenet",
    augment: bool = False,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Load a split into (X, y, class_names) with X shaped (N, 224, 224, 3)."""
    if split_name not in SPLITS:
        raise ValueError(f"Invalid split '{split_name}'. Expected one of {SPLITS}.")
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
            images.append(preprocess_image(pil_img, normalization=normalization, expand_dims=False))
            labels.append(class_idx)
    if not images:
        return (
            np.empty((0, IMAGE_SIZE[1], IMAGE_SIZE[0], 3), dtype=np.float32),
            np.empty((0,), dtype=np.int64),
            list(CLASS_NAMES),
        )
    return np.stack(images).astype(np.float32), np.array(labels, dtype=np.int64), list(CLASS_NAMES)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="AnimalCare AI dataset organisation and preprocessing")
    parser.add_argument("--dataset-dir", default=DEFAULT_DATASET_DIR, help="Path to the ml/dataset directory")
    parser.add_argument("--init", action="store_true", help="Create raw/, train/, val/ and test/ class folders")
    parser.add_argument("--seed-samples", action="store_true", help="Generate SYNTHETIC placeholder images and split them")
    parser.add_argument("--organize", action="store_true", help="Split real images from raw/<class>/ into train/val/test")
    parser.add_argument("--verify", action="store_true", help="Report image counts per split and the data source")
    parser.add_argument("--image", type=str, default=None, help="Preprocess one image and print tensor stats")
    args = parser.parse_args()

    if args.init:
        info = init_dataset_directories(args.dataset_dir)
        print(f"Initialized {len(info['directories'])} dataset directories under {info['dataset_root']}.")
    if args.seed_samples:
        print("Generating SYNTHETIC placeholder images (not real animals)...")
        print(json.dumps(seed_sample_dataset(args.dataset_dir), indent=2))
    if args.organize:
        print(json.dumps(organize_raw_dataset(dataset_root=args.dataset_dir), indent=2))
    if args.image:
        batch = preprocess_image(args.image, expand_dims=True)
        print(f"Preprocessed '{args.image}' -> shape={batch.shape}, min={batch.min():.3f}, max={batch.max():.3f}")
    if args.verify or not (args.init or args.seed_samples or args.organize or args.image):
        print(json.dumps(verify_dataset_structure(args.dataset_dir), indent=2))


if __name__ == "__main__":
    main()
