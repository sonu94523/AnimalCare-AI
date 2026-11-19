# AnimalCare AI – Dataset Organization

This directory contains the image dataset structure for training and evaluating the **MobileNetV2** transfer learning model on **Cow** and **Buffalo** disease images.

## Supported Classes
1. `healthy` – Healthy Cow / Buffalo baseline images
2. `lumpy_skin_disease` – Lumpy Skin Disease (LSD) images showing nodular skin lesions
3. `foot_and_mouth_disease` – Foot-and-Mouth Disease (FMD) images showing mouth/muzzle/hoof vesicles

## Directory Layout
```text
ml/dataset/
├── class_indices.json
├── raw/
│   ├── healthy/
│   ├── lumpy_skin_disease/
│   └── foot_and_mouth_disease/
├── train/                  # 70% split
│   ├── healthy/
│   ├── lumpy_skin_disease/
│   └── foot_and_mouth_disease/
├── val/                    # 15% split
│   ├── healthy/
│   ├── lumpy_skin_disease/
│   └── foot_and_mouth_disease/
└── test/                   # 15% split
    ├── healthy/
    ├── lumpy_skin_disease/
    └── foot_and_mouth_disease/
```

## Usage Commands
Initialize folders and seed sample verification images:
```bash
python ml/preprocessing.py --init --seed-samples --verify
```

Organize your own raw images placed inside `ml/dataset/raw/<class_name>/`:
```bash
python ml/preprocessing.py --organize --verify
```
