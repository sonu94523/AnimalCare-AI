"""Shared ML constants that do not require PyTorch to import."""

import os

ML_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SAVED_MODELS_DIR = os.path.join(ML_DIR, "saved_models")

WEIGHTS_FILENAME = "mobilenetv2_animalcare.pt"
ARCHITECTURE_FILENAME = "model_architecture.json"
TRAINING_HISTORY_FILENAME = "training_history.json"
EVALUATION_METRICS_FILENAME = "evaluation_metrics.json"

# Image predictions below this top-class probability are reported as uncertain.
LOW_CONFIDENCE_THRESHOLD = 60.0

MODEL_STATUS_NOTE = (
    "This image model has not been validated on real animals. Unless it was retrained on "
    "real labelled photos, it was trained on synthetic placeholder images, so its output only "
    "demonstrates the pipeline and must not be used as a diagnosis."
)
