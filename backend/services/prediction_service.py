"""
MobileNetV2 image inference service (fail-closed).

- Never trains a model inside an HTTP request. If the checkpoint is missing or
  corrupted, raises `ModelUnavailableError` so the API returns HTTP 503.
- Guards singleton model loading with a `threading.Lock`.
- Rejects blank / uniform / near-zero-detail images (e.g. solid black or solid
  white) before classification so they never receive a confident disease label
  or quarantine advice.
- Clearly marks predictions with `trainingData`, `modelValidated`, and a
  non-diagnostic status note.
"""

import json
import logging
import os
import threading
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

from backend.domain_data import CONDITION_PREVENTION
from ml.constants import DEFAULT_SAVED_MODELS_DIR, LOW_CONFIDENCE_THRESHOLD, MODEL_STATUS_NOTE
from ml.model import MobileNetV2DiseaseModel, weights_path_for
from ml.preprocessing import (
    CLASS_DISPLAY_NAMES,
    IMAGE_SIZE,
    SUPPORTED_ANIMALS,
    load_rgb_image,
    normalize_pixels,
)

logger = logging.getLogger(__name__)

# Images whose per-channel pixel standard deviation (on 0..255 scale) is below
# this threshold have almost no visual texture (e.g. solid black/white frames).
MIN_IMAGE_STD_THRESHOLD = 5.0

_MODEL_LOCK = threading.Lock()
_MODEL_CACHE: Dict[str, Tuple[float, MobileNetV2DiseaseModel]] = {}


class ModelUnavailableError(RuntimeError):
    """Raised when no valid trained MobileNetV2 checkpoint is available."""


CONDITION_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "healthy": {
        "diseaseSlug": "healthy",
        "summary": "Demo image output leaned toward the Healthy class (not clinically validated).",
        "prevention": CONDITION_PREVENTION["healthy"],
    },
    "lumpy_skin_disease": {
        "diseaseSlug": "lumpy_skin_disease",
        "summary": "Demo image output leaned toward Lumpy Skin Disease (not clinically validated; verify with symptoms and a veterinarian).",
        "prevention": CONDITION_PREVENTION["lumpy_skin_disease"],
    },
    "foot_and_mouth_disease": {
        "diseaseSlug": "foot_and_mouth_disease",
        "summary": "Demo image output leaned toward Foot-and-Mouth Disease (not clinically validated; verify with symptoms and a veterinarian).",
        "prevention": CONDITION_PREVENTION["foot_and_mouth_disease"],
    },
}

UNSUITABLE_IMAGE_GUIDANCE = [
    "Upload a clear, well-lit photograph showing the animal's skin, muzzle, or hooves.",
    "Use the Symptom Checker to record observed clinical signs.",
    "Consult a qualified veterinarian for any suspected illness.",
]


def clear_model_cache() -> None:
    """Clear the cached model instances (useful in tests)."""
    with _MODEL_LOCK:
        _MODEL_CACHE.clear()


def is_model_available(models_dir: str = DEFAULT_SAVED_MODELS_DIR) -> bool:
    return os.path.isfile(weights_path_for(models_dir))


def get_trained_model(models_dir: str = DEFAULT_SAVED_MODELS_DIR) -> MobileNetV2DiseaseModel:
    """Load the saved checkpoint under a thread lock; fail closed if missing."""
    ckpt_path = weights_path_for(models_dir)
    if not os.path.isfile(ckpt_path):
        raise ModelUnavailableError(
            "Image classification model weights are not installed. "
            "Train a checkpoint first with `python -m ml.train`."
        )

    mtime = os.path.getmtime(ckpt_path)
    with _MODEL_LOCK:
        cached = _MODEL_CACHE.get(ckpt_path)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        try:
            model = MobileNetV2DiseaseModel.from_checkpoint(ckpt_path)
        except (OSError, ValueError, RuntimeError, KeyError) as exc:
            logger.error("Failed to load model checkpoint %s: %s", ckpt_path, exc)
            raise ModelUnavailableError(
                f"Model checkpoint at {os.path.basename(ckpt_path)} could not be loaded. "
                "Retrain with `python -m ml.train`."
            ) from exc
        _MODEL_CACHE[ckpt_path] = (mtime, model)
        return model


def _read_class_display_order(model: MobileNetV2DiseaseModel, dataset_dir: Optional[str] = None) -> list:
    """Use class order from checkpoint, cross-checked against class_indices.json if present."""
    if dataset_dir:
        ci_path = os.path.join(dataset_dir, "class_indices.json")
        if os.path.isfile(ci_path):
            try:
                with open(ci_path, "r", encoding="utf-8") as f:
                    mapping = json.load(f).get("class_indices", {})
                if isinstance(mapping, dict) and len(mapping) == len(model.class_names):
                    ordered = [k for k, _ in sorted(mapping.items(), key=lambda kv: kv[1])]
                    if ordered != model.class_names:
                        logger.warning(
                            "class_indices.json order %s differs from checkpoint order %s; using checkpoint order.",
                            ordered,
                            model.class_names,
                        )
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Could not read class_indices.json: %s", exc)
    return list(model.class_names)


def _check_visual_suitability(rgb_array: np.ndarray) -> Optional[str]:
    """Basic out-of-distribution guard rejecting solid/blank/uniform frames."""
    pixel_std = float(rgb_array.std())
    if pixel_std < MIN_IMAGE_STD_THRESHOLD:
        return (
            f"Image has almost no visual detail (pixel std = {pixel_std:.2f}, e.g. solid black, "
            "solid white, or blank frame) and cannot be classified as an animal photograph."
        )
    return None


def predict_disease_from_image(
    image_source: Union[str, os.PathLike, bytes],
    animal_id: str = "cow",
    models_dir: str = DEFAULT_SAVED_MODELS_DIR,
    dataset_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Run MobileNetV2 inference with fail-closed loading and OOD blank-image screening."""
    normalized_animal = (animal_id or "cow").strip().lower()
    if normalized_animal not in SUPPORTED_ANIMALS:
        raise ValueError(
            f"AI image detection is unavailable for '{normalized_animal}'. "
            "Only Cow and Buffalo are supported."
        )

    model = get_trained_model(models_dir=models_dir)
    class_names = _read_class_display_order(model, dataset_dir=dataset_dir)

    pil_img = load_rgb_image(image_source, target_size=IMAGE_SIZE)
    rgb_array = np.asarray(pil_img, dtype=np.float32)

    ood_reason = _check_visual_suitability(rgb_array)
    if ood_reason is not None:
        return {
            "animalId": normalized_animal,
            "predictedClass": "uncertain",
            "predictedLabel": "Uncertain / Unsuitable Image",
            "imagePrediction": "Uncertain / Unsuitable Image (Not an Animal Photo)",
            "confidence": 0.0,
            "isLowConfidence": True,
            "isOutOfDistribution": True,
            "lowConfidenceThreshold": LOW_CONFIDENCE_THRESHOLD,
            "uncertaintyNotice": ood_reason,
            "classProbabilities": [
                {
                    "classId": cname,
                    "label": CLASS_DISPLAY_NAMES.get(cname, cname),
                    "probabilityPercent": 0.0,
                }
                for cname in class_names
            ],
            "summary": ood_reason,
            "preventionTips": UNSUITABLE_IMAGE_GUIDANCE,
            "modelBackbone": "MobileNetV2",
            "trainingData": model.training_data,
            "modelValidated": False,
            "modelStatusNote": MODEL_STATUS_NOTE,
            "inputShape": [1, IMAGE_SIZE[1], IMAGE_SIZE[0], 3],
        }

    tensor = np.expand_dims(normalize_pixels(rgb_array, mode=model.normalization), axis=0)
    probs = model.predict_proba(tensor)[0]

    top_idx = int(probs.argmax())
    predicted_class = class_names[top_idx]
    predicted_label = CLASS_DISPLAY_NAMES.get(predicted_class, predicted_class)
    confidence_percent = round(float(probs[top_idx]) * 100.0, 2)
    is_low_confidence = confidence_percent < LOW_CONFIDENCE_THRESHOLD

    class_probabilities = [
        {
            "classId": cname,
            "label": CLASS_DISPLAY_NAMES.get(cname, cname),
            "probabilityPercent": round(float(probs[idx]) * 100.0, 2),
        }
        for idx, cname in enumerate(class_names)
    ]

    guidance = CONDITION_GUIDANCE.get(predicted_class, CONDITION_GUIDANCE["healthy"])
    if is_low_confidence:
        display_prediction = f"Uncertain / Low Confidence ({predicted_label})"
        uncertainty_notice = (
            f"Model confidence ({confidence_percent}%) is below the {LOW_CONFIDENCE_THRESHOLD}% "
            "threshold. Please use the Symptom Checker and consult a qualified veterinarian."
        )
    else:
        display_prediction = f"{predicted_label} (Demo Model — Not Validated)"
        uncertainty_notice = None

    return {
        "animalId": normalized_animal,
        "predictedClass": predicted_class,
        "predictedLabel": predicted_label,
        "imagePrediction": display_prediction,
        "confidence": confidence_percent,
        "isLowConfidence": is_low_confidence,
        "isOutOfDistribution": False,
        "lowConfidenceThreshold": LOW_CONFIDENCE_THRESHOLD,
        "uncertaintyNotice": uncertainty_notice,
        "classProbabilities": class_probabilities,
        "summary": guidance["summary"],
        "preventionTips": guidance["prevention"],
        "modelBackbone": "MobileNetV2",
        "trainingData": model.training_data,
        "modelValidated": False,
        "modelStatusNote": MODEL_STATUS_NOTE,
        "inputShape": list(tensor.shape),
    }
