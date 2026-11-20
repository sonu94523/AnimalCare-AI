"""
Evaluate a trained checkpoint on a held-out split.

Run from the project root:
    python -m ml.evaluate --split test

Computes accuracy, per-class precision/recall/F1, macro and weighted averages,
and the confusion matrix, then writes evaluation_metrics.json next to the weights.
"""

import argparse
import json
import logging
import os
from typing import Any, Dict, List, Sequence

import numpy as np

from ml.constants import DEFAULT_SAVED_MODELS_DIR, EVALUATION_METRICS_FILENAME, LOW_CONFIDENCE_THRESHOLD
from ml.model import MobileNetV2DiseaseModel, weights_path_for
from ml.preprocessing import CLASS_DISPLAY_NAMES, DEFAULT_DATASET_DIR, load_split_arrays, read_dataset_source

logger = logging.getLogger(__name__)


def compute_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> List[List[int]]:
    """Rows are true classes, columns are predicted classes."""
    matrix = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        if 0 <= int(t) < num_classes and 0 <= int(p) < num_classes:
            matrix[int(t), int(p)] += 1
    return matrix.tolist()


def compute_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_names: Sequence[str]) -> Dict[str, Any]:
    """Accuracy, per-class precision/recall/F1/support and macro/weighted averages (in %)."""
    class_names = list(class_names)
    cm = np.array(compute_confusion_matrix(y_true, y_pred, len(class_names)), dtype=np.float64)
    total = int(cm.sum())
    accuracy = float(np.trace(cm) / total * 100.0) if total else 0.0

    per_class: Dict[str, Dict[str, Any]] = {}
    precisions, recalls, f1s, supports = [], [], [], []
    for idx, cname in enumerate(class_names):
        tp = cm[idx, idx]
        fp = cm[:, idx].sum() - tp
        fn = cm[idx, :].sum() - tp
        support = int(cm[idx, :].sum())
        precision = tp / (tp + fp) * 100.0 if (tp + fp) else 0.0
        recall = tp / (tp + fn) * 100.0 if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        supports.append(support)
        per_class[cname] = {
            "displayName": CLASS_DISPLAY_NAMES.get(cname, cname),
            "precision": round(precision, 2),
            "recall": round(recall, 2),
            "f1Score": round(f1, 2),
            "support": support,
        }

    weights = np.array(supports, dtype=np.float64) / total if total else np.zeros(len(class_names))
    return {
        "totalSamples": total,
        "accuracyPercent": round(accuracy, 2),
        "macroAvg": {
            "precision": round(float(np.mean(precisions)), 2),
            "recall": round(float(np.mean(recalls)), 2),
            "f1Score": round(float(np.mean(f1s)), 2),
        },
        "weightedAvg": {
            "precision": round(float(np.sum(np.array(precisions) * weights)), 2),
            "recall": round(float(np.sum(np.array(recalls) * weights)), 2),
            "f1Score": round(float(np.sum(np.array(f1s) * weights)), 2),
        },
        "perClass": per_class,
        "confusionMatrix": {"labels": class_names, "matrix": cm.astype(int).tolist()},
    }


def evaluate_saved_model(
    dataset_root: str = DEFAULT_DATASET_DIR,
    saved_models_dir: str = DEFAULT_SAVED_MODELS_DIR,
    split_name: str = "test",
) -> Dict[str, Any]:
    weights_path = weights_path_for(saved_models_dir)
    if not os.path.isfile(weights_path):
        raise FileNotFoundError(f"No trained model at {weights_path}. Run `python -m ml.train` first.")
    model = MobileNetV2DiseaseModel.from_checkpoint(weights_path)

    X_eval, y_eval, _ = load_split_arrays(split_name, dataset_root=dataset_root, normalization=model.normalization)
    if X_eval.shape[0] == 0:
        raise FileNotFoundError(f"No images in the '{split_name}' split of {dataset_root}.")

    probs = model.predict_proba(X_eval)
    y_pred = probs.argmax(axis=1)
    confidences = probs.max(axis=1) * 100.0

    report = {
        "modelName": "AnimalCare_MobileNetV2",
        "evaluatedSplit": split_name,
        "trainingData": model.training_data,
        "evaluationData": read_dataset_source(dataset_root)["source"],
        "validated": False,
        **compute_classification_metrics(y_eval, y_pred, model.class_names),
        "confidenceSummary": {
            "lowConfidenceThresholdPercent": LOW_CONFIDENCE_THRESHOLD,
            "meanConfidencePercent": round(float(confidences.mean()), 2),
            "minConfidencePercent": round(float(confidences.min()), 2),
            "maxConfidencePercent": round(float(confidences.max()), 2),
            "lowConfidenceCount": int((confidences < LOW_CONFIDENCE_THRESHOLD).sum()),
        },
    }
    os.makedirs(saved_models_dir, exist_ok=True)
    out_path = os.path.join(saved_models_dir, EVALUATION_METRICS_FILENAME)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return {"evaluation_path": out_path, "report": report}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Evaluate the trained MobileNetV2 model")
    parser.add_argument("--dataset-dir", default=DEFAULT_DATASET_DIR)
    parser.add_argument("--models-dir", default=DEFAULT_SAVED_MODELS_DIR)
    parser.add_argument("--split", default="test", choices=["train", "val", "test"])
    args = parser.parse_args()

    result = evaluate_saved_model(args.dataset_dir, args.models_dir, args.split)
    report = result["report"]
    print(f"=== Evaluation on '{args.split}' split ({report['totalSamples']} images, data: {report['evaluationData']}) ===")
    print(f"Accuracy : {report['accuracyPercent']:.2f}%")
    print(f"Macro F1 : {report['macroAvg']['f1Score']:.2f}%")
    for metrics in report["perClass"].values():
        print(
            f"  - {metrics['displayName']:<30} P: {metrics['precision']:6.2f}%  R: {metrics['recall']:6.2f}%  "
            f"F1: {metrics['f1Score']:6.2f}%  n={metrics['support']}"
        )
    print("Confusion matrix (rows=true, cols=pred):", report["confusionMatrix"]["matrix"])
    print(f"Saved to: {result['evaluation_path']}")
    if report["evaluationData"] == "synthetic":
        print("WARNING: evaluated on synthetic placeholder images. This accuracy says nothing about real animals.")


if __name__ == "__main__":
    main()
