"""
MobileNetV2 disease classifier (PyTorch / torchvision).

Architecture: MobileNetV2 feature extractor -> global average pooling ->
Dense(128, ReLU) -> Dropout(0.3) -> Dense(num_classes).

By default the backbone starts from ImageNet weights (transfer learning) and is
frozen, except for the top blocks unfrozen with `unfreeze_top_layers`. Inputs are
224x224 RGB tensors normalised with ImageNet mean/std (see
`ml.preprocessing.normalize_pixels`). There is no other input path into the
classifier: predictions come only from the CNN features.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models as tv_models

from ml.constants import ARCHITECTURE_FILENAME, DEFAULT_SAVED_MODELS_DIR, WEIGHTS_FILENAME
from ml.preprocessing import CLASS_DISPLAY_NAMES, CLASS_NAMES, IMAGE_SHAPE, SUPPORTED_ANIMALS

logger = logging.getLogger(__name__)

NORMALIZATION = "imagenet"


class PretrainedWeightsUnavailableError(RuntimeError):
    """Raised when ImageNet weights were requested but could not be loaded."""


def weights_path_for(models_dir: str = DEFAULT_SAVED_MODELS_DIR) -> str:
    return os.path.join(models_dir, WEIGHTS_FILENAME)


def _build_backbone(pretrained: bool) -> nn.Module:
    if not pretrained:
        return tv_models.mobilenet_v2(weights=None)
    try:
        return tv_models.mobilenet_v2(weights=tv_models.MobileNet_V2_Weights.IMAGENET1K_V1)
    except (OSError, RuntimeError) as exc:
        raise PretrainedWeightsUnavailableError(
            f"Could not download or load ImageNet weights for MobileNetV2 ({exc}). "
            "Check your internet connection, or pass --no-pretrained to deliberately "
            "train from random initialisation."
        ) from exc


class TorchMobileNetV2Classifier(nn.Module):
    """MobileNetV2 features + global average pooling + small dense classification head."""

    def __init__(self, num_classes: int, dense_units: int = 128, dropout_rate: float = 0.3, pretrained: bool = True):
        super().__init__()
        backbone = _build_backbone(pretrained)
        self.features = backbone.features
        self.feature_dim = backbone.last_channel  # 1280
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(self.feature_dim, dense_units),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(dense_units, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier_head(self.global_pool(self.features(x)))


class MobileNetV2DiseaseModel:
    """Wrapper handling training, inference, checkpoints and metadata."""

    def __init__(
        self,
        class_names: Sequence[str] = CLASS_NAMES,
        dense_units: int = 128,
        dropout_rate: float = 0.3,
        learning_rate: float = 1e-3,
        freeze_base: bool = True,
        pretrained: bool = True,
        training_data: str = "unknown",
    ):
        self.class_names: List[str] = list(class_names)
        self.num_classes = len(self.class_names)
        self.dense_units = dense_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.pretrained = pretrained
        self.training_data = training_data
        self.normalization = NORMALIZATION
        self.unfrozen_top_blocks = 0
        self.model = TorchMobileNetV2Classifier(self.num_classes, dense_units, dropout_rate, pretrained)
        self.set_backbone_frozen(freeze_base)

    # ------------------------------------------------------------------ setup
    def set_backbone_frozen(self, frozen: bool) -> None:
        self.freeze_base = frozen
        for param in self.model.features.parameters():
            param.requires_grad = not frozen

    def unfreeze_top_layers(self, num_blocks: int = 2) -> Dict[str, int]:
        """Make the last `num_blocks` feature blocks trainable for fine-tuning."""
        for block in list(self.model.features.children())[-num_blocks:]:
            for param in block.parameters():
                param.requires_grad = True
        self.unfrozen_top_blocks = num_blocks
        return self.count_parameters()

    def count_parameters(self) -> Dict[str, int]:
        total = sum(p.numel() for p in self.model.parameters())
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        return {"totalParams": int(total), "trainableParams": int(trainable), "frozenParams": int(total - trainable)}

    # -------------------------------------------------------------- inference
    @staticmethod
    def _to_nchw_tensor(batch_nhwc: np.ndarray) -> torch.Tensor:
        arr = np.asarray(batch_nhwc, dtype=np.float32)
        if arr.ndim == 3:
            arr = arr[None]
        if arr.ndim != 4 or arr.shape[-1] != 3:
            raise ValueError(f"Expected input shaped (N, H, W, 3), got {arr.shape}")
        return torch.from_numpy(np.ascontiguousarray(arr.transpose(0, 3, 1, 2)))

    def predict_proba(self, batch_nhwc: np.ndarray) -> np.ndarray:
        """Return class probabilities (N, num_classes) for preprocessed (N, 224, 224, 3) input."""
        x = self._to_nchw_tensor(batch_nhwc)
        if tuple(x.shape[2:]) != IMAGE_SHAPE[:2]:
            raise ValueError(f"Expected 224x224 images, got {tuple(x.shape[2:])}")
        self.model.eval()
        with torch.no_grad():
            return torch.softmax(self.model(x), dim=1).cpu().numpy().astype(np.float32)

    # --------------------------------------------------------------- training
    @staticmethod
    def _augment_batch(bx: torch.Tensor, gen: torch.Generator) -> torch.Tensor:
        """Apply per-epoch on-the-fly augmentation to an (N, 3, H, W) tensor batch.

        Runs inside `fit()` so every epoch sees fresh random variants while the
        original `X_train` array remains intact.
        """
        out = bx.clone()
        n, _, h, w = out.shape
        for i in range(n):
            sample = out[i]
            # 1. Random horizontal flip (50% chance)
            if float(torch.rand(1, generator=gen).item()) < 0.5:
                sample = torch.flip(sample, dims=[2])

            # 2. Random zoom crop (90% to 100%) resized back to (h, w)
            scale = 0.90 + 0.10 * float(torch.rand(1, generator=gen).item())
            if scale < 0.99:
                ch, cw = max(1, int(h * scale)), max(1, int(w * scale))
                top = int(torch.randint(0, h - ch + 1, (1,), generator=gen).item())
                left = int(torch.randint(0, w - cw + 1, (1,), generator=gen).item())
                cropped = sample[:, top:top + ch, left:left + cw].unsqueeze(0)
                sample = F.interpolate(cropped, size=(h, w), mode="bilinear", align_corners=False).squeeze(0)

            # 3. Mild multiplicative contrast & additive brightness jitter
            contrast = 0.88 + 0.24 * float(torch.rand(1, generator=gen).item())
            brightness = -0.12 + 0.24 * float(torch.rand(1, generator=gen).item())
            sample = sample * contrast + brightness
            out[i] = sample
        return out

    def _set_train_mode(self) -> None:
        self.model.train()
        if self.pretrained:
            # Keep ImageNet BatchNorm statistics fixed while fine-tuning on a small dataset.
            for module in self.model.features.modules():
                if isinstance(module, nn.BatchNorm2d):
                    module.eval()

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        epochs: int = 8,
        batch_size: int = 8,
        seed: int = 42,
        augment: bool = False,
    ) -> Dict[str, Any]:
        """Train with Adam + cross-entropy and optional per-epoch on-the-fly augmentation.

        With a validation set, the weights from the epoch with the best validation
        accuracy (ties broken by lower validation loss) are restored at the end.
        Without one, the final epoch's weights are kept.
        """
        if len(X_train) == 0:
            raise ValueError("Training array X_train is empty.")
        torch.manual_seed(seed)
        rng = np.random.default_rng(seed)
        aug_gen = torch.Generator().manual_seed(seed)

        optimizer = torch.optim.Adam([p for p in self.model.parameters() if p.requires_grad], lr=self.learning_rate)
        criterion = nn.CrossEntropyLoss()
        x_train = self._to_nchw_tensor(X_train)
        y_train_t = torch.as_tensor(np.asarray(y_train), dtype=torch.long)
        has_val = X_val is not None and len(X_val) > 0
        if has_val:
            x_val = self._to_nchw_tensor(X_val)
            y_val_t = torch.as_tensor(np.asarray(y_val), dtype=torch.long)

        history: List[Dict[str, Any]] = []
        best_score = None
        best_epoch = epochs
        best_state = None
        n_train = x_train.shape[0]

        for epoch in range(1, epochs + 1):
            self._set_train_mode()
            perm = torch.from_numpy(rng.permutation(n_train))
            total_loss, correct = 0.0, 0
            for start in range(0, n_train, batch_size):
                idx = perm[start:start + batch_size]
                bx, by = x_train[idx], y_train_t[idx]
                if augment:
                    bx = self._augment_batch(bx, aug_gen)
                optimizer.zero_grad()
                logits = self.model(bx)
                loss = criterion(logits, by)
                loss.backward()
                optimizer.step()
                total_loss += float(loss.item()) * len(idx)
                correct += int((logits.argmax(dim=1) == by).sum())

            entry: Dict[str, Any] = {
                "epoch": epoch,
                "trainLoss": round(total_loss / n_train, 4),
                "trainAccuracy": round(correct / n_train * 100.0, 2),
                "valLoss": None,
                "valAccuracy": None,
            }
            if has_val:
                self.model.eval()
                with torch.no_grad():
                    v_logits = self.model(x_val)
                    v_loss = float(criterion(v_logits, y_val_t).item())
                    v_acc = float((v_logits.argmax(dim=1) == y_val_t).float().mean().item() * 100.0)
                entry["valLoss"], entry["valAccuracy"] = round(v_loss, 4), round(v_acc, 2)
                score = (v_acc, -v_loss)
                if best_score is None or score > best_score:
                    best_score, best_epoch = score, epoch
                    best_state = {k: v.detach().clone() for k, v in self.model.state_dict().items()}
            history.append(entry)

        if best_state is not None:
            self.model.load_state_dict(best_state)
        self.model.eval()
        return {
            "epochsCompleted": epochs,
            "batchSize": batch_size,
            "learningRate": self.learning_rate,
            "bestEpoch": best_epoch,
            "selectionMetric": "val_accuracy" if has_val else "last_epoch",
            "bestValAccuracy": round(best_score[0], 2) if best_score else None,
            "history": history,
        }

    # --------------------------------------------------------- persistence
    def get_architecture_summary(self) -> Dict[str, Any]:
        return {
            "modelName": "AnimalCare_MobileNetV2",
            "backbone": "MobileNetV2",
            "framework": "pytorch",
            "pretrainedBackbone": self.pretrained,
            "inputShape": list(IMAGE_SHAPE),
            "normalization": "imagenet mean/std",
            "supportedAnimals": list(SUPPORTED_ANIMALS),
            "classNames": self.class_names,
            "classDisplayNames": {c: CLASS_DISPLAY_NAMES.get(c, c) for c in self.class_names},
            "frozenBackbone": self.freeze_base,
            "unfrozenTopBlocks": self.unfrozen_top_blocks,
            "head": [
                {"layer": "GlobalAveragePooling2D", "outputFeatures": 1280},
                {"layer": "Dense", "units": self.dense_units, "activation": "relu"},
                {"layer": "Dropout", "rate": self.dropout_rate},
                {"layer": "Dense", "units": self.num_classes, "activation": "softmax (at inference)"},
            ],
            "optimizer": {"name": "Adam", "learningRate": self.learning_rate},
            "loss": "cross_entropy",
            "parameters": self.count_parameters(),
            "trainingData": self.training_data,
            "validated": False,
        }

    def save_architecture_metadata(self, saved_models_dir: str = DEFAULT_SAVED_MODELS_DIR) -> str:
        os.makedirs(saved_models_dir, exist_ok=True)
        out_path = os.path.join(saved_models_dir, ARCHITECTURE_FILENAME)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(self.get_architecture_summary(), f, indent=2)
        return out_path

    def save_checkpoint(self, saved_models_dir: str = DEFAULT_SAVED_MODELS_DIR) -> str:
        os.makedirs(saved_models_dir, exist_ok=True)
        out_path = weights_path_for(saved_models_dir)
        torch.save(
            {
                "format_version": 2,
                "state_dict": self.model.state_dict(),
                "class_names": self.class_names,
                "dense_units": self.dense_units,
                "dropout_rate": self.dropout_rate,
                "pretrained": self.pretrained,
                "normalization": self.normalization,
                "training_data": self.training_data,
            },
            out_path,
        )
        return out_path

    @classmethod
    def from_checkpoint(cls, weights_path: str) -> "MobileNetV2DiseaseModel":
        """Load a checkpoint written by `save_checkpoint` (class order comes from the file)."""
        checkpoint = torch.load(weights_path, map_location="cpu", weights_only=True)
        if not isinstance(checkpoint, dict) or checkpoint.get("format_version") != 2:
            raise ValueError("Unsupported checkpoint format. Retrain with `python -m ml.train`.")
        instance = cls(
            class_names=checkpoint["class_names"],
            dense_units=checkpoint["dense_units"],
            dropout_rate=checkpoint["dropout_rate"],
            pretrained=False,  # architecture only; the trained weights are loaded below
            training_data=checkpoint.get("training_data", "unknown"),
        )
        instance.pretrained = bool(checkpoint.get("pretrained", False))
        instance.normalization = checkpoint.get("normalization", NORMALIZATION)
        instance.model.load_state_dict(checkpoint["state_dict"])
        instance.model.eval()
        return instance
