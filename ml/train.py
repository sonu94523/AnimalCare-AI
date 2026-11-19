"""
MobileNetV2 Transfer Learning Training Pipeline & Model Checkpointing.

Loads preprocessed 224x224x3 train and validation splits from `ml/dataset/`,
trains the MobileNetV2 classification head for Cow & Buffalo disease detection
(`healthy`, `lumpy_skin_disease`, `foot_and_mouth_disease`), and saves the best
trained weights and training history to `ml/saved_models/`.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict

ML_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ML_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.model import (
    DEFAULT_SAVED_MODELS_DIR,
    MobileNetV2DiseaseModel,
    resolve_writable_models_dir,
)
from ml.preprocessing import (
    CLASS_DISPLAY_NAMES,
    CLASS_NAMES,
    DEFAULT_DATASET_DIR,
    load_split_arrays,
    seed_sample_dataset,
)


def verify_model_forward_pass(
    model: MobileNetV2DiseaseModel,
    dataset_root: str = DEFAULT_DATASET_DIR,
) -> Dict[str, Any]:
    """
    Load a validation batch from `ml/dataset/` (seeding samples if empty), run a
    forward pass through the MobileNetV2 transfer learning model, and verify the
    output probability tensor shape (N, 3) and probability sum (1.0).
    """
    X_val, y_val, _ = load_split_arrays("val", dataset_root=dataset_root)
    if X_val.shape[0] == 0:
        seed_sample_dataset(dataset_root=dataset_root)
        X_val, y_val, _ = load_split_arrays("val", dataset_root=dataset_root)

    sample_batch = X_val[:4]
    probs = model.predict_proba(sample_batch)
    pred_indices = probs.argmax(axis=1).tolist()
    pred_classes = [CLASS_NAMES[idx] for idx in pred_indices]
    pred_labels = [CLASS_DISPLAY_NAMES[c] for c in pred_classes]

    return {
        "input_batch_shape": list(sample_batch.shape),
        "output_probs_shape": list(probs.shape),
        "row_probability_sums": [round(float(s), 4) for s in probs.sum(axis=1)],
        "sample_predictions": [
            {
                "sample_index": i,
                "predicted_class": pred_classes[i],
                "predicted_label": pred_labels[i],
                "confidence_percent": round(float(probs[i, pred_indices[i]]) * 100.0, 2),
            }
            for i in range(len(pred_indices))
        ],
    }


def train_and_save_model(
    dataset_root: str = DEFAULT_DATASET_DIR,
    saved_models_dir: str = DEFAULT_SAVED_MODELS_DIR,
    epochs: int = 8,
    batch_size: int = 8,
    learning_rate: float = 1e-3,
    dense_units: int = 128,
    dropout_rate: float = 0.3,
    unfreeze_top: int = 2,
    pretrained: bool = False,
    augment: bool = True,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Train the MobileNetV2 transfer learning model on `ml/dataset/train` and
    validate on `ml/dataset/val`, then save the trained checkpoint and history.
    """
    X_train, y_train, _ = load_split_arrays(
        "train",
        dataset_root=dataset_root,
        augment=augment,
        seed=seed,
    )
    X_val, y_val, _ = load_split_arrays(
        "val",
        dataset_root=dataset_root,
        augment=False,
        seed=seed,
    )

    if X_train.shape[0] == 0:
        seed_sample_dataset(dataset_root=dataset_root, seed=seed)
        X_train, y_train, _ = load_split_arrays(
            "train",
            dataset_root=dataset_root,
            augment=augment,
            seed=seed,
        )
        X_val, y_val, _ = load_split_arrays(
            "val",
            dataset_root=dataset_root,
            augment=False,
            seed=seed,
        )

    model = MobileNetV2DiseaseModel(
        num_classes=len(CLASS_NAMES),
        dense_units=dense_units,
        dropout_rate=dropout_rate,
        learning_rate=learning_rate,
        freeze_base=True,
        pretrained=pretrained,
    )

    if unfreeze_top > 0:
        model.unfreeze_top_layers(unfreeze_top)

    training_report = model.fit(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        epochs=epochs,
        batch_size=batch_size,
        seed=seed,
    )

    arch_path = model.save_architecture_metadata(saved_models_dir)
    weights_path = model.save_weights(saved_models_dir)

    target_dir = resolve_writable_models_dir(saved_models_dir)
    history_path = os.path.join(target_dir, "training_history.json")

    full_report = {
        "model_name": "AnimalCare_MobileNetV2",
        "backbone": "MobileNetV2",
        "framework_backend": model.backend,
        "dataset_sizes": {
            "train_samples": int(X_train.shape[0]),
            "val_samples": int(X_val.shape[0]),
        },
        "class_names": list(CLASS_NAMES),
        "weights_file": os.path.basename(weights_path),
        **training_report,
    }

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    return {
        "architecture_path": arch_path,
        "weights_path": weights_path,
        "history_path": history_path,
        "report": full_report,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train MobileNetV2 Transfer Learning Model for AnimalCare AI"
    )
    parser.add_argument(
        "--dataset-dir",
        default=DEFAULT_DATASET_DIR,
        help="Path to the ml/dataset directory",
    )
    parser.add_argument(
        "--models-dir",
        default=DEFAULT_SAVED_MODELS_DIR,
        help="Directory to save model weights and training history",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=8,
        help="Number of training epochs (default: 8)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Mini-batch size (default: 8)",
    )
    parser.add_argument(
        "--dense-units",
        type=int,
        default=128,
        help="Units in the custom Dense hidden layer (default: 128)",
    )
    parser.add_argument(
        "--dropout",
        type=float,
        default=0.3,
        help="Dropout rate in the custom classification head (default: 0.3)",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-3,
        help="Initial Adam learning rate (default: 0.001)",
    )
    parser.add_argument(
        "--unfreeze-top",
        type=int,
        default=2,
        help="Unfreeze top N backbone blocks during training (default: 2)",
    )
    parser.add_argument(
        "--pretrained",
        action="store_true",
        help="Download/use pretrained ImageNet weights if available",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only print architecture summary without running training epochs",
    )
    parser.add_argument(
        "--verify-forward",
        action="store_true",
        help="Run a forward pass verification on a validation batch",
    )
    args = parser.parse_args()

    if args.summary_only:
        model = MobileNetV2DiseaseModel(
            num_classes=len(CLASS_NAMES),
            dense_units=args.dense_units,
            dropout_rate=args.dropout,
            learning_rate=args.lr,
            freeze_base=True,
            pretrained=args.pretrained,
        )
        summary = model.get_architecture_summary()
        print("=== AnimalCare AI: MobileNetV2 Architecture Summary ===")
        print(json.dumps(summary, indent=2))
        if args.verify_forward:
            print("\n=== Forward-Pass Verification ===")
            print(json.dumps(verify_model_forward_pass(model, args.dataset_dir), indent=2))
        return

    result = train_and_save_model(
        dataset_root=args.dataset_dir,
        saved_models_dir=args.models_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        dense_units=args.dense_units,
        dropout_rate=args.dropout,
        unfreeze_top=args.unfreeze_top,
        pretrained=args.pretrained,
    )

    print("=== AnimalCare AI: MobileNetV2 Training Complete ===")
    for item in result["report"]["history"]:
        print(
            f"Epoch {item['epoch']:02d}/{args.epochs:02d} - "
            f"train_loss: {item['train_loss']:.4f} - train_acc: {item['train_accuracy']:.2f}% - "
            f"val_loss: {item['val_loss']:.4f} - val_acc: {item['val_accuracy']:.2f}%"
        )
    print(
        f"\nBest Epoch: {result['report']['best_epoch']} "
        f"(Val Accuracy: {result['report']['best_val_accuracy']:.2f}%)"
    )
    print(f"Saved weights to: {result['weights_path']}")
    print(f"Saved training history to: {result['history_path']}")


if __name__ == "__main__":
    main()
