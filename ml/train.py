"""
Train the MobileNetV2 classifier and save the checkpoint plus metadata.

Run from the project root:
    python -m ml.preprocessing --init --seed-samples   # synthetic demo data only
    python -m ml.train --epochs 8

Training on the synthetic sample data produces a model that recognises the
generated colour patterns, not disease. The saved metadata records the data
source so the API and UI can say so.
"""

import argparse
import json
import logging
import os
from typing import Any, Dict

from ml.constants import DEFAULT_SAVED_MODELS_DIR, TRAINING_HISTORY_FILENAME
from ml.model import MobileNetV2DiseaseModel
from ml.preprocessing import CLASS_NAMES, DEFAULT_DATASET_DIR, load_split_arrays, read_dataset_source

logger = logging.getLogger(__name__)


def train_and_save_model(
    dataset_root: str = DEFAULT_DATASET_DIR,
    saved_models_dir: str = DEFAULT_SAVED_MODELS_DIR,
    epochs: int = 8,
    batch_size: int = 8,
    learning_rate: float = 1e-3,
    dense_units: int = 128,
    dropout_rate: float = 0.3,
    unfreeze_top: int = 2,
    pretrained: bool = True,
    augment: bool = True,
    seed: int = 42,
) -> Dict[str, Any]:
    """Train on ml/dataset/train with per-epoch augmentation, select on val, and save artefacts."""
    # Always load original un-augmented images; augmentation runs fresh per batch inside fit().
    X_train, y_train, _ = load_split_arrays("train", dataset_root=dataset_root, augment=False, seed=seed)
    if X_train.shape[0] == 0:
        raise FileNotFoundError(
            f"No training images found in {os.path.join(dataset_root, 'train')}. Add real labelled images to "
            "ml/dataset/raw/<class_name>/ and run `python -m ml.preprocessing --organize`, or generate synthetic "
            "demo data with `python -m ml.preprocessing --init --seed-samples`."
        )
    X_val, y_val, _ = load_split_arrays("val", dataset_root=dataset_root, augment=False, seed=seed)

    source = read_dataset_source(dataset_root)["source"]
    if source == "synthetic":
        logger.warning("Training on SYNTHETIC placeholder images: the resulting model cannot detect real disease.")

    model = MobileNetV2DiseaseModel(
        class_names=CLASS_NAMES,
        dense_units=dense_units,
        dropout_rate=dropout_rate,
        learning_rate=learning_rate,
        freeze_base=True,
        pretrained=pretrained,
        training_data=source,
    )
    if unfreeze_top > 0:
        model.unfreeze_top_layers(unfreeze_top)

    report = model.fit(X_train, y_train, X_val, y_val, epochs=epochs, batch_size=batch_size, seed=seed, augment=augment)

    weights_path = model.save_checkpoint(saved_models_dir)
    arch_path = model.save_architecture_metadata(saved_models_dir)
    history = {
        "modelName": "AnimalCare_MobileNetV2",
        "backbone": "MobileNetV2",
        "framework": "pytorch",
        "pretrainedBackbone": pretrained,
        "trainingData": source,
        "validated": False,
        "datasetSizes": {"trainSamples": int(X_train.shape[0]), "valSamples": int(X_val.shape[0])},
        "classNames": list(CLASS_NAMES),
        "weightsFile": os.path.basename(weights_path),
        **report,
    }
    history_path = os.path.join(saved_models_dir, TRAINING_HISTORY_FILENAME)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return {"weights_path": weights_path, "architecture_path": arch_path, "history_path": history_path, "report": history}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Train the AnimalCare AI MobileNetV2 classifier")
    parser.add_argument("--dataset-dir", default=DEFAULT_DATASET_DIR)
    parser.add_argument("--models-dir", default=DEFAULT_SAVED_MODELS_DIR)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--dense-units", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.3)
    parser.add_argument("--unfreeze-top", type=int, default=2, help="Backbone blocks to fine-tune (default: 2)")
    parser.add_argument("--no-pretrained", action="store_true", help="Start from random weights instead of ImageNet")
    parser.add_argument("--summary-only", action="store_true", help="Print the architecture without training")
    args = parser.parse_args()

    if args.summary_only:
        model = MobileNetV2DiseaseModel(dense_units=args.dense_units, dropout_rate=args.dropout, pretrained=not args.no_pretrained)
        print(json.dumps(model.get_architecture_summary(), indent=2))
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
        pretrained=not args.no_pretrained,
    )
    report = result["report"]
    print(f"Training data: {report['trainingData']} | pretrained backbone: {report['pretrainedBackbone']}")
    for item in report["history"]:
        val = (
            f"val_loss: {item['valLoss']:.4f} - val_acc: {item['valAccuracy']:.2f}%"
            if item["valLoss"] is not None
            else "no validation set"
        )
        print(f"Epoch {item['epoch']:02d} - train_loss: {item['trainLoss']:.4f} - train_acc: {item['trainAccuracy']:.2f}% - {val}")
    print(f"Saved weights to: {result['weights_path']}")
    if report["trainingData"] == "synthetic":
        print("WARNING: trained on synthetic placeholder images. These numbers say nothing about real animals.")


if __name__ == "__main__":
    main()
