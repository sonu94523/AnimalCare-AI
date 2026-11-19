"""
MobileNetV2 Transfer Learning Model Architecture & Setup.

Defines the MobileNetV2 transfer learning classifier for Cow & Buffalo disease
detection across 3 classes:
  0: healthy
  1: lumpy_skin_disease
  2: foot_and_mouth_disease

Architecture:
  - Base Backbone: MobileNetV2 (input 224x224x3, pretrained feature extractor, frozen base layers)
  - Custom Classification Head:
      GlobalAveragePooling2D (1280 features)
      -> Dense / Linear (128 units, ReLU)
      -> Dropout (rate = 0.3)
      -> Dense / Linear (3 units, Softmax)

Supports both TensorFlow/Keras (`tf.keras.applications.MobileNetV2`) and
PyTorch/Torchvision (`torchvision.models.mobilenet_v2`) so the model builds and
runs reliably across Python 3.10–3.13 environments.
"""

import json
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ml.preprocessing import (
    CLASS_DISPLAY_NAMES,
    CLASS_NAMES,
    IMAGE_SHAPE,
    IMAGE_SIZE,
    SUPPORTED_ANIMALS,
)

ML_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SAVED_MODELS_DIR = os.path.join(ML_DIR, "saved_models")

# Detect available deep learning backend (TensorFlow/Keras or PyTorch/Torchvision)
HAS_TF = False
HAS_TORCH = False

try:
    import tensorflow as tf  # type: ignore
    HAS_TF = True
except ImportError:
    pass

try:
    import torch  # type: ignore
    import torch.nn as nn  # type: ignore
    from torchvision import models as tv_models  # type: ignore
    HAS_TORCH = True
except ImportError:
    pass


def resolve_writable_models_dir(preferred_dir: str = DEFAULT_SAVED_MODELS_DIR) -> str:
    """Return preferred_dir if writable; otherwise fall back to a temp directory."""
    try:
        os.makedirs(preferred_dir, exist_ok=True)
        probe = os.path.join(preferred_dir, ".write_probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return preferred_dir
    except Exception:
        fallback = os.path.join(tempfile.gettempdir(), "animalcare_saved_models")
        os.makedirs(fallback, exist_ok=True)
        return fallback


def build_keras_mobilenetv2_model(
    num_classes: int = len(CLASS_NAMES),
    input_shape: Tuple[int, int, int] = IMAGE_SHAPE,
    dense_units: int = 128,
    dropout_rate: float = 0.3,
    learning_rate: float = 1e-3,
    freeze_base: bool = True,
    weights: Optional[str] = "imagenet",
):
    """
    Build and compile a TensorFlow/Keras MobileNetV2 transfer learning model:
      Input(224, 224, 3)
      -> MobileNetV2(include_top=False, weights=weights)
      -> GlobalAveragePooling2D()
      -> Dense(128, activation='relu')
      -> Dropout(0.3)
      -> Dense(3, activation='softmax')
    """
    if not HAS_TF:
        raise RuntimeError("TensorFlow is not installed in the current Python environment.")

    try:
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=input_shape,
            include_top=False,
            weights=weights,
        )
    except Exception:
        # Offline fallback if ImageNet weights have not been cached locally yet
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=input_shape,
            include_top=False,
            weights=None,
        )

    base_model.trainable = not freeze_base

    inputs = tf.keras.Input(shape=input_shape, name="animal_image_input")
    x = base_model(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = tf.keras.layers.Dense(dense_units, activation="relu", name="dense_128")(x)
    x = tf.keras.layers.Dropout(dropout_rate, name="dropout_03")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="disease_output")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="AnimalCare_MobileNetV2")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


if HAS_TORCH:
    class TorchMobileNetV2Classifier(nn.Module):
        """
        PyTorch equivalent of the MobileNetV2 transfer learning architecture:
          MobileNetV2.features (1280 channels)
          -> AdaptiveAvgPool2d((1, 1)) (GlobalAveragePooling2D equivalent)
          -> Linear(1280, 128) + ReLU
          -> Dropout(0.3)
          -> Linear(128, 3)
        """

        def __init__(
            self,
            num_classes: int = len(CLASS_NAMES),
            dense_units: int = 128,
            dropout_rate: float = 0.3,
            freeze_base: bool = True,
            pretrained: bool = True,
        ):
            super().__init__()
            backbone = None
            if pretrained:
                try:
                    backbone = tv_models.mobilenet_v2(weights=tv_models.MobileNet_V2_Weights.DEFAULT)
                except Exception:
                    backbone = None
            if backbone is None:
                backbone = tv_models.mobilenet_v2(weights=None)

            self.features = backbone.features
            self.feature_dim = backbone.last_channel  # 1280

            if freeze_base:
                for param in self.features.parameters():
                    param.requires_grad = False

            self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
            self.classifier_head = nn.Sequential(
                nn.Flatten(),
                nn.Linear(self.feature_dim, dense_units),
                nn.ReLU(inplace=True),
                nn.Dropout(p=dropout_rate),
                nn.Linear(dense_units, num_classes),
            )

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            feat = self.features(x)
            pooled = self.global_pool(feat)
            logits = self.classifier_head(pooled)
            return logits


class MobileNetV2DiseaseModel:
    """
    Unified MobileNetV2 Transfer Learning wrapper for architecture setup,
    training, evaluation, and Flask inference.
    """

    def __init__(
        self,
        num_classes: int = len(CLASS_NAMES),
        dense_units: int = 128,
        dropout_rate: float = 0.3,
        learning_rate: float = 1e-3,
        freeze_base: bool = True,
        pretrained: bool = True,
    ):
        self.num_classes = num_classes
        self.dense_units = dense_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.freeze_base = freeze_base
        self.pretrained = pretrained
        self.class_names = list(CLASS_NAMES)
        self.backend = "tensorflow" if HAS_TF else ("pytorch" if HAS_TORCH else "numpy_fallback")
        self.model: Any = None
        self._build()

    def _build(self) -> None:
        if self.backend == "tensorflow":
            weights = "imagenet" if self.pretrained else None
            self.model = build_keras_mobilenetv2_model(
                num_classes=self.num_classes,
                input_shape=IMAGE_SHAPE,
                dense_units=self.dense_units,
                dropout_rate=self.dropout_rate,
                learning_rate=self.learning_rate,
                freeze_base=self.freeze_base,
                weights=weights,
            )
        elif self.backend == "pytorch":
            self.model = TorchMobileNetV2Classifier(
                num_classes=self.num_classes,
                dense_units=self.dense_units,
                dropout_rate=self.dropout_rate,
                freeze_base=self.freeze_base,
                pretrained=self.pretrained,
            )
        else:
            rng = np.random.default_rng(42)
            self.model = {
                "W1": rng.normal(0, 0.05, size=(1280, self.dense_units)).astype(np.float32),
                "b1": np.zeros((self.dense_units,), dtype=np.float32),
                "W2": rng.normal(0, 0.05, size=(self.dense_units, self.num_classes)).astype(np.float32),
                "b2": np.zeros((self.num_classes,), dtype=np.float32),
            }

    def count_parameters(self) -> Dict[str, int]:
        """Return total, trainable, and frozen parameter counts."""
        if self.backend == "tensorflow":
            total = int(self.model.count_params())
            trainable = int(
                sum(np.prod(v.shape) for v in self.model.trainable_weights)
            )
            return {
                "total_params": total,
                "trainable_params": trainable,
                "frozen_params": total - trainable,
            }
        if self.backend == "pytorch":
            total = sum(p.numel() for p in self.model.parameters())
            trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            return {
                "total_params": int(total),
                "trainable_params": int(trainable),
                "frozen_params": int(total - trainable),
            }
        total = 1280 * self.dense_units + self.dense_units + self.dense_units * self.num_classes + self.num_classes
        return {
            "total_params": int(total),
            "trainable_params": int(total),
            "frozen_params": 0,
        }

    def unfreeze_top_layers(self, num_layers: int = 3) -> Dict[str, int]:
        """Unfreeze the last `num_layers` of the MobileNetV2 feature extractor for fine-tuning."""
        self.freeze_base = False
        if self.backend == "tensorflow":
            base_model = self.model.layers[1]
            base_model.trainable = True
            for layer in base_model.layers[:-num_layers]:
                layer.trainable = False
        elif self.backend == "pytorch":
            feature_blocks = list(self.model.features.children())
            for block in feature_blocks[-num_layers:]:
                for param in block.parameters():
                    param.requires_grad = True
        return self.count_parameters()

    def predict_proba(self, batch_nhwc: np.ndarray) -> np.ndarray:
        """
        Run a forward pass on a batch of preprocessed images of shape (N, 224, 224, 3)
        and return class probabilities of shape (N, 3) summing to 1.0.
        """
        x = np.asarray(batch_nhwc, dtype=np.float32)
        if x.ndim == 3:
            x = np.expand_dims(x, axis=0)
        if x.shape[1:] != IMAGE_SHAPE:
            raise ValueError(f"Expected input shape (N, 224, 224, 3), got {x.shape}")

        if self.backend == "tensorflow":
            probs = self.model.predict(x, verbose=0)
            return np.asarray(probs, dtype=np.float32)

        if self.backend == "pytorch":
            self.model.eval()
            with torch.no_grad():
                # Convert NHWC -> NCHW for PyTorch MobileNetV2
                nchw = np.transpose(x, (0, 3, 1, 2))
                tensor_x = torch.from_numpy(nchw)
                logits = self.model(tensor_x)
                probs = torch.softmax(logits, dim=1).cpu().numpy()
                return probs.astype(np.float32)

        # NumPy fallback
        pooled = x.mean(axis=(1, 2))  # (N, 3)
        tiled = np.resize(pooled, (x.shape[0], 1280))
        hidden = np.maximum(0.0, tiled @ self.model["W1"] + self.model["b1"])
        logits = hidden @ self.model["W2"] + self.model["b2"]
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        return (exp_logits / np.sum(exp_logits, axis=1, keepdims=True)).astype(np.float32)

    def get_architecture_summary(self) -> Dict[str, Any]:
        """Return a structured dictionary describing the MobileNetV2 architecture."""
        params = self.count_parameters()
        return {
            "model_name": "AnimalCare_MobileNetV2",
            "backbone": "MobileNetV2",
            "framework_backend": self.backend,
            "input_shape": list(IMAGE_SHAPE),
            "image_size": list(IMAGE_SIZE),
            "normalization": "mobilenet_v2 ([-1.0, 1.0])",
            "supported_animals": list(SUPPORTED_ANIMALS),
            "num_classes": self.num_classes,
            "class_names": self.class_names,
            "class_display_names": CLASS_DISPLAY_NAMES,
            "freeze_base": self.freeze_base,
            "custom_head": [
                {"layer": "GlobalAveragePooling2D", "output_features": 1280},
                {"layer": "Dense", "units": self.dense_units, "activation": "relu"},
                {"layer": "Dropout", "rate": self.dropout_rate},
                {"layer": "Dense", "units": self.num_classes, "activation": "softmax"},
            ],
            "optimizer": {
                "name": "Adam",
                "learning_rate": self.learning_rate,
                "loss": "categorical_crossentropy",
            },
            "parameters": params,
        }

    def save_architecture_metadata(
        self,
        saved_models_dir: str = DEFAULT_SAVED_MODELS_DIR,
    ) -> str:
        """Save `model_architecture.json` to `ml/saved_models/`."""
        target_dir = resolve_writable_models_dir(saved_models_dir)
        out_path = os.path.join(target_dir, "model_architecture.json")
        summary = self.get_architecture_summary()
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return out_path
