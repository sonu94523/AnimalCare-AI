# AnimalCare AI – Dataset Organization

This directory holds image splits for training and evaluating the PyTorch **MobileNetV2** classifier for **Cow** and **Buffalo** images.

> **Important:** No real animal photographs are bundled in this repository. Running `python -m ml.preprocessing --init --seed-samples` generates **synthetic coloured-noise placeholder images** solely to verify that the preprocessing, training and evaluation code runs end to end. A model trained on those synthetic placeholders learns colour patterns, **not** disease, and is not clinically valid.

## Supported Classes
1. `healthy` – Healthy Cow / Buffalo images
2. `lumpy_skin_disease` – Lumpy Skin Disease (LSD) images
3. `foot_and_mouth_disease` – Foot-and-Mouth Disease (FMD) images

## Directory Layout
```text
ml/dataset/
├── class_indices.json
├── dataset_source.json        # Records "synthetic" vs "user_provided"
├── raw/                       # Place REAL labelled photos here before --organize
│   ├── healthy/
│   ├── lumpy_skin_disease/
│   └── foot_and_mouth_disease/
├── train/                     # 70% split
├── val/                       # 15% split
└── test/                      # 15% split
```

## Usage Commands (run from project root)
Train on **your own real labelled dataset** (place images in `ml/dataset/raw/<class_name>/` first):
```bash
python -m ml.preprocessing --organize --verify
python -m ml.train --epochs 10
python -m ml.evaluate --split test
```

Generate **synthetic placeholder data** for local pipeline testing only:
```bash
python -m ml.preprocessing --init --seed-samples --verify
python -m ml.train --epochs 8
python -m ml.evaluate --split test
```
