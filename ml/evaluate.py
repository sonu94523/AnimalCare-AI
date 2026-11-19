"""
Model Evaluation, Confusion Matrix & Classification Metrics Pipeline.

Loads the trained MobileNetV2 model checkpoint from `ml/saved_models/`,
evaluates predictions on the held-out `test` split (`ml/dataset/test/`),
computes accuracy, per-class precision/recall/F1-score, macro/weighted averages,
and the 3x3 confusion matrix, and saves `evaluation_metrics.json`.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

import numpy as np

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
from ml.train import train_and_save_model

LOW_CONFIDENCE_THRESHOLD = 60.0  # Percent threshold below which prediction is flagged uncertain


def compute_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    num_classes: int = len(CLASS_NAMES),
) -> List[List[int]]:
    """Compute a num_classes x num_classes confusion matrix (rows=true, cols=pred)."""
    matrix = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        if 0 <= int(t) < num_classes and 0 <= int(p) < num_classes:
            matrix[int(t), int(p)] += 1
    return matrix.tolist()


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: List[str] = list(CLASS_NAMES),
) -> Dict[str, Any]:
    """
    Compute overall accuracy, per-class precision, recall, F1-score, support,
    and macro/weighted averages without requiring external metric libraries.
    """
    num_classes = len(class_names)
    cm = np.array(compute_confusion_matrix(y_true, y_pred, num_classes), dtype=np.float64)
    total_samples = int(cm.sum())
    overall_acc = float(np.trace(cm) / total_samples * 100.0) if total_samples > 0 else 0.0

    per_class: Dict[str, Dict[str, Any]] = {}
    precisions: List[float] = []
    recalls: List[float] = []
    f1s: List[float] = []
    supports: List[int] = []

    for idx, cname in enumerate(class_names):
        tp = float(cm[idx, idx])
        fp = float(cm[:, idx].sum() - tp)
        fn = float(cm[idx, :].sum() - tp)
        support = int(cm[idx, :].sum())

        precision = (tp / (tp + fp) * 100.0) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn) * 100.0) if (tp + fn) > 0 else 0.0
        f1 = (
            (2.0 * precision * recall / (precision + recall))
            if (precision + recall) > 0
            else 0.0
        )

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        supports.append(support)

        per_class[cname] = {
            "display_name": CLASS_DISPLAY_NAMES.get(cname, cname),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1_score": round(f1, 2),
            "support": support,
        }

    macro_precision = float(np.mean(precisions)) if precisions else 0.0
    macro_recall = float(np.mean(recalls)) if recalls else 0.0
    macro_f1 = float(np.mean(f1s)) if f1s else 0.0

    if total_samples > 0:
        weights = np.array(supports, dtype=np.float64) / total_samples
        weighted_precision = float(np.sum(np.array(precisions) * weights))
        weighted_recall = float(np.sum(np.array(recalls) * weights))
        weighted_f1 = float(np.sum(np.array(f1s) * weights))
    else:
        weighted_precision = weighted_recall = weighted_f1 = 0.0

    return {
        "total_samples": total_samples,
        "accuracy_percent": round(overall_acc, 2),
        "macro_avg": {
            "precision": round(macro_precision, 2),
            "recall": round(macro_recall, 2),
            "f1_score": round(macro_f1, 2),
        },
        "weighted_avg": {
            "precision": round(weighted_precision, 2),
            "recall": round(weighted_recall, 2),
            "f1_score": round(weighted_f1, 2),
        },
        "per_class": per_class,
        "confusion_matrix": {
            "labels": class_names,
            "matrix": cm.astype(int).tolist(),
        },
    }


def evaluate_saved_model(
    dataset_root: str = DEFAULT_DATASET_DIR,
    saved_models_dir: str = DEFAULT_SAVED_MODELS_DIR,
    split_name: str = "test",
) -> Dict[str, Any]:
    """
    Evaluate the saved MobileNetV2 model on `split_name` ('test' by default)
    and write `evaluation_metrics.json` to `ml/saved_models/`.
    """
    X_eval, y_eval, class_names = load_split_arrays(
        split_name,
        dataset_root=dataset_root,
        augment=False,
    )
    if X_eval.shape[0] == 0:
        seed_sample_dataset(dataset_root=dataset_root)
        X_eval, y_eval, class_names = load_split_arrays(
            split_name,
            dataset_root=dataset_root,
            augment=False,
        )

    model = MobileNetV2DiseaseModel(
        num_classes=len(class_names),
        freeze_base=True,
        pretrained=False,
    )
    weights_loaded = model.load_weights(saved_models_dir=saved_models_dir)
    if not weights_loaded:
        # Train and save a fresh checkpoint if none exists yet
        train_and_save_model(
            dataset_root=dataset_root,
            saved_models_dir=saved_models_dir,
            epochs=8,
        )
        weights_loaded = model.load_weights(saved_models_dir=saved_models_dir)

    probs = model.predict_proba(X_eval)
    y_pred = probs.argmax(axis=1)
    max_confidences = probs.max(axis=1) * 100.0

    metrics = compute_classification_metrics(y_eval, y_pred, class_names)

    low_conf_count = int((max_confidences < LOW_CONFIDENCE_THRESHOLD).sum())
    confidence_summary = {
        "low_confidence_threshold_percent": LOW_CONFIDENCE_THRESHOLD,
        "mean_confidence_percent": round(float(max_confidences.mean()), 2),
        "min_confidence_percent": round(float(max_confidences.min()), 2),
        "max_confidence_percent": round(float(max_confidences.max()), 2),
        "low_confidence_count": low_conf_count,
    }

    report = {
        "model_name": "AnimalCare_MobileNetV2",
        "backbone": "MobileNetV2",
        "framework_backend": model.backend,
        "evaluated_split": split_name,
        "weights_loaded": weights_loaded,
        **metrics,
        "confidence_summary": confidence_summary,
    }

    target_dir = resolve_writable_models_dir(saved_models_dir)
    out_path = os.path.join(target_dir, "evaluation_metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return {
        "evaluation_path": out_path,
        "report": report,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Trained MobileNetV2 Model & Compute Confusion Matrix"
    )
    parser.add_argument(
        "--dataset-dir",
        default=DEFAULT_DATASET_DIR,
        help="Path to the ml/dataset directory",
    )
    parser.add_argument(
        "--models-dir",
        default=DEFAULT_SAVED_MODELS_DIR,
        help="Path to the ml/saved_models directory",
    )
    parser.add_argument(
        "--split",
        default="test",
        choices=["train", "val", "test"],
        help="Dataset split to evaluate (default: test)",
    )
    args = parser.parse_args()

    result = evaluate_saved_model(
        dataset_root=args.dataset_dir,
        saved_models_dir=args.models_dir,
        split_name=args.split,
    )
    report = result["report"]

    print(f"=== AnimalCare AI: MobileNetV2 Evaluation ({args.split.upper()} Split) ===")
    print(f"Total Samples : {report['total_samples']}")
    print(f"Accuracy      : {report['accuracy_percent']:.2f}%")
    print(
        f"Macro F1      : {report['macro_avg']['f1_score']:.2f}% "
        f"(Precision: {report['macro_avg']['precision']:.2f}%, Recall: {report['macro_avg']['recall']:.2f}%)"
    )
    print("\nPer-Class Metrics:")
    for cname, cmetrics in report["per_class"].items():
        print(
            f"  - {cmetrics['display_name']:<30} | "
            f"P: {cmetrics['precision']:6.2f}% | "
            f"R: {cmetrics['recall']:6.2f}% | "
            f"F1: {cmetrics['f1_score']:6.2f}% | "
            f"Support: {cmetrics['support']}"
        )
    print("\nConfusion Matrix (rows=true, cols=pred):")
    print(json.dumps(report["confusion_matrix"], indent=2))
    print(f"\nSaved evaluation metrics to: {result['evaluation_path']}")


if __name__ == "__main__":
    main()
