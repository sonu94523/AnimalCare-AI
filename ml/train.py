"""
MobileNetV2 Transfer Learning Architecture Setup & Forward-Pass Verification.
"""

import argparse
import json
import os
import sys

ML_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ML_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.model import DEFAULT_SAVED_MODELS_DIR, MobileNetV2DiseaseModel
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
) -> dict:
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


def main():
    parser = argparse.ArgumentParser(
        description="Build MobileNetV2 Transfer Learning Architecture & Verify Forward Pass"
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
        default=0,
        help="Optionally unfreeze top N backbone blocks for fine-tuning (default: 0 = frozen base)",
    )
    parser.add_argument(
        "--no-pretrained",
        action="store_true",
        help="Initialize MobileNetV2 without downloading pretrained ImageNet weights",
    )
    parser.add_argument(
        "--verify-forward",
        action="store_true",
        help="Run a forward pass on a preprocessed 224x224x3 batch",
    )
    args = parser.parse_args()

    model = MobileNetV2DiseaseModel(
        num_classes=len(CLASS_NAMES),
        dense_units=args.dense_units,
        dropout_rate=args.dropout,
        learning_rate=args.lr,
        freeze_base=True,
        pretrained=not args.no_pretrained,
    )

    if args.unfreeze_top > 0:
        model.unfreeze_top_layers(args.unfreeze_top)

    metadata_path = model.save_architecture_metadata(DEFAULT_SAVED_MODELS_DIR)
    summary = model.get_architecture_summary()

    print("=== AnimalCare AI: MobileNetV2 Architecture Summary ===")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved architecture metadata to: {metadata_path}")

    if args.verify_forward:
        forward_report = verify_model_forward_pass(model)
        print("\n=== Forward-Pass Verification ===")
        print(json.dumps(forward_report, indent=2))


if __name__ == "__main__":
    main()
