"""
MobileNetV2 Image Inference Service for Cow & Buffalo Disease Screening.

Loads the trained MobileNetV2 transfer learning checkpoint and runs 224x224 RGB
inference, returning class probabilities, top prediction, confidence score,
honest low-confidence uncertainty warnings (< 60%), and preventive care tips.
"""

import os
import sys
from typing import Any, Dict, Optional, Union

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.evaluate import LOW_CONFIDENCE_THRESHOLD
from ml.model import DEFAULT_SAVED_MODELS_DIR, MobileNetV2DiseaseModel
from ml.preprocessing import (
    CLASS_DISPLAY_NAMES,
    CLASS_NAMES,
    DEFAULT_DATASET_DIR,
    IMAGE_SIZE,
    SUPPORTED_ANIMALS,
    preprocess_image,
)
from ml.train import train_and_save_model

_MODEL_INSTANCE: Optional[MobileNetV2DiseaseModel] = None

CONDITION_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "healthy": {
        "diseaseSlug": "healthy",
        "summary": "No visual signs of Lumpy Skin Disease or Foot-and-Mouth Disease nodules/blisters detected.",
        "prevention": [
            "Continue balanced nutrition, clean drinking water, and dry shelter hygiene.",
            "Follow routine regional vaccination schedules for LSD and FMD.",
            "Monitor appetite, body temperature, and milk yield daily.",
        ],
    },
    "lumpy_skin_disease": {
        "diseaseSlug": "lsd",
        "summary": "Visual features resemble nodular skin lesions associated with Lumpy Skin Disease (LSD).",
        "prevention": [
            "Immediately isolate the affected animal from the rest of the herd.",
            "Control blood-feeding insect vectors (mosquitoes, biting flies, ticks) in sheds.",
            "Disinfect equipment and contact a veterinarian for confirmatory diagnosis.",
        ],
    },
    "foot_and_mouth_disease": {
        "diseaseSlug": "fmd",
        "summary": "Visual features resemble blister/vesicle lesions associated with Foot-and-Mouth Disease (FMD).",
        "prevention": [
            "Strictly quarantine the animal and restrict livestock movement.",
            "Disinfect feeding troughs, footbaths, and footwear immediately.",
            "Contact a local veterinary officer for examination and supportive care.",
        ],
    },
}


def get_trained_model() -> MobileNetV2DiseaseModel:
    """Return a singleton MobileNetV2DiseaseModel loaded with trained weights."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE

    model = MobileNetV2DiseaseModel(
        num_classes=len(CLASS_NAMES),
        freeze_base=True,
        pretrained=False,
    )
    loaded = model.load_weights(saved_models_dir=DEFAULT_SAVED_MODELS_DIR)
    if not loaded:
        train_and_save_model(
            dataset_root=DEFAULT_DATASET_DIR,
            saved_models_dir=DEFAULT_SAVED_MODELS_DIR,
            epochs=8,
        )
        model.load_weights(saved_models_dir=DEFAULT_SAVED_MODELS_DIR)

    _MODEL_INSTANCE = model
    return _MODEL_INSTANCE


def predict_disease_from_image(
    image_source: Union[str, bytes],
    animal_id: str = "cow",
) -> Dict[str, Any]:
    """
    Preprocess an uploaded Cow or Buffalo image to (1, 224, 224, 3) and run
    MobileNetV2 classification.
    """
    normalized_animal = (animal_id or "cow").strip().lower()
    if normalized_animal not in SUPPORTED_ANIMALS:
        raise ValueError(
            f"AI image detection is unavailable for '{normalized_animal}'. "
            "Only Cow and Buffalo are supported."
        )

    tensor = preprocess_image(
        image_source,
        target_size=IMAGE_SIZE,
        normalization="mobilenet_v2",
        expand_dims=True,
    )

    model = get_trained_model()
    probs = model.predict_proba(tensor)[0]  # shape (3,)

    top_idx = int(probs.argmax())
    predicted_class = CLASS_NAMES[top_idx]
    predicted_label = CLASS_DISPLAY_NAMES.get(predicted_class, predicted_class)
    confidence_percent = round(float(probs[top_idx]) * 100.0, 2)
    is_low_confidence = confidence_percent < LOW_CONFIDENCE_THRESHOLD

    class_probabilities = [
        {
            "classId": cname,
            "label": CLASS_DISPLAY_NAMES.get(cname, cname),
            "probabilityPercent": round(float(probs[idx]) * 100.0, 2),
        }
        for idx, cname in enumerate(CLASS_NAMES)
    ]

    guidance = CONDITION_GUIDANCE.get(predicted_class, CONDITION_GUIDANCE["healthy"])
    if is_low_confidence:
        display_prediction = f"Uncertain / Low Confidence ({predicted_label})"
        uncertainty_notice = (
            f"Model confidence ({confidence_percent}%) is below the {LOW_CONFIDENCE_THRESHOLD}% "
            "reliability threshold. Image features are ambiguous—please use the Symptom Checker "
            "and consult a qualified veterinarian."
        )
    else:
        display_prediction = predicted_label
        uncertainty_notice = None

    return {
        "animalId": normalized_animal,
        "predictedClass": predicted_class,
        "predictedLabel": predicted_label,
        "imagePrediction": display_prediction,
        "confidence": confidence_percent,
        "isLowConfidence": is_low_confidence,
        "lowConfidenceThreshold": LOW_CONFIDENCE_THRESHOLD,
        "uncertaintyNotice": uncertainty_notice,
        "classProbabilities": class_probabilities,
        "summary": guidance["summary"],
        "preventionTips": guidance["prevention"],
        "modelBackbone": "MobileNetV2",
        "inputShape": list(tensor.shape),
    }
