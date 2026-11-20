# AnimalCare AI – Animal Disease Detection System

A college-level web application for preliminary animal disease screening combining a **weighted rule-based clinical symptom checker**, a **PyTorch MobileNetV2 image classification pipeline**, and an **explicit agree/conflict/uncertainty decision service**.

> **Honest Status of the Image Model (Demo Only — Not Clinically Validated):**
> No real animal disease image dataset is shipped with this repository. Unless you place real labelled cow/buffalo photos in `ml/dataset/raw/` and retrain, any locally generated checkpoint is trained only on **synthetic placeholder images** created by `ml/preprocessing.py --seed-samples`. Predictions from a synthetic-trained model demonstrate the technical pipeline only and **cannot detect real disease**. If no trained checkpoint exists on disk, the backend fails closed with **HTTP 503** rather than returning random predictions.

---

## Key Features
- **6 Animal Categories Displayed:**
  - **Demo Image + Symptom Screening:** **Cow**, **Buffalo**
  - **Symptom Reference Only (AI Image Detection Unavailable):** **Goat**, **Sheep**, **Dog**, **Cat** (blocked server-side for image inference)
- **PyTorch MobileNetV2 Transfer Learning Pipeline (`ml/`):**
  - Preprocesses uploaded JPG/JPEG/PNG photos (`max 5 MB`, `MAX_IMAGE_PIXELS = 25M`) by re-encoding through PIL to strip EXIF/GPS metadata, resizing to `224 × 224` RGB, and applying ImageNet mean/std normalization.
  - Defaults to `pretrained=True` (`MobileNet_V2_Weights.IMAGENET1K_V1`) with `AdaptiveAvgPool2d -> Linear(1280, 128) -> ReLU -> Dropout(0.3) -> Linear(128, 3)`.
  - Rejects blank/solid/low-detail frames (e.g. solid black or solid white) before classification as **Out-of-Distribution / Unsuitable Image**, and flags predictions under `60%` confidence as uncertain.
- **Weighted Rule-Based Symptom Checker (`backend/services/symptom_service.py`):**
  - Evaluates hallmark vs. supporting clinical signs across all 6 animal categories.
  - Prevents single non-specific signs (such as fever alone) from claiming a specific disease.
- **Server-Side Combined Decision Engine (`backend/services/decision_service.py`):**
  - Cross-checks server-stored image predictions (looked up strictly by server-issued `uploadId`, never trusting client-submitted predictions or paths) against clinical symptoms, reporting **Agreement**, **Conflict / Disagreement Detected**, or **Partial / Low-Confidence Evidence**.
- **Security & Storage Hardening:**
  - Defaults to `HOST=127.0.0.1`, `FLASK_DEBUG=0`, and CORS restricted to `http://localhost:5173,http://127.0.0.1:5173`.
  - Destructive history endpoints (`DELETE /api/history`, `DELETE /api/history/<id>`) fail closed unless `ADMIN_TOKEN` is configured and matched via `X-Admin-Token`, and clean up associated uploaded image files on disk.
  - Uploaded images are served with `X-Content-Type-Options: nosniff`.

---

## REST API Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Backend health check, AI-supported animals, and model load status |
| `GET` | `/api/animals` | List all 6 animal categories and AI support status |
| `GET` | `/api/symptoms` | List clinical symptoms (supports `?animal=cow` filter) |
| `POST` | `/api/symptoms/submit` | Run rule-based symptom analysis and save screening record |
| `GET` | `/api/diseases` | List reference information for supported conditions |
| `POST` | `/api/upload` | Validate, strip EXIF, classify (if model loaded), and return a server-side `uploadId` |
| `POST` | `/api/predict/image` | Upload, classify with MobileNetV2 (returns `503` if no checkpoint), and save history |
| `POST` | `/api/predict/combined` | Combine server-side `uploadId` (or uploaded file) with symptoms |
| `GET` | `/api/model/info` | Inspect MobileNetV2 architecture, load status, training source & validation notice |
| `GET` | `/api/history` | List saved prediction history (supports `?animal=cow` filter) |
| `GET` | `/api/history/<id>` | Retrieve a single saved prediction record |
| `DELETE` | `/api/history/<id>` | Delete a record and its uploaded file *(requires `X-Admin-Token`)* |
| `DELETE` | `/api/history` | Clear all history and uploaded files *(requires `X-Admin-Token`)* |

---

## Setup & Execution

All Python commands should be run from the **project root** (`AnimalCare-AI/`).

### 1. Backend & ML Environment
**Windows (PowerShell):**
```powershell
python -m venv backend\venv
.\backend\venv\Scripts\pip.exe install -r backend\requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv backend/venv
backend/venv/bin/pip install -r backend/requirements.txt
```

### 2. Prepare a Model Checkpoint (Required for Image Screening)
If no checkpoint exists in `ml/saved_models/mobilenetv2_animalcare.pt`, image endpoints intentionally return **HTTP 503** (symptom screening continues to work).

- **With real labelled cow/buffalo photos:** place images inside `ml/dataset/raw/{healthy,lumpy_skin_disease,foot_and_mouth_disease}/` and run:
  ```powershell
  .\backend\venv\Scripts\python.exe -m ml.preprocessing --organize --verify
  .\backend\venv\Scripts\python.exe -m ml.train --epochs 10
  .\backend\venv\Scripts\python.exe -m ml.evaluate --split test
  ```
- **For a local synthetic pipeline demo only (not real disease detection):**
  ```powershell
  .\backend\venv\Scripts\python.exe -m ml.preprocessing --init --seed-samples --verify
  .\backend\venv\Scripts\python.exe -m ml.train --epochs 8
  .\backend\venv\Scripts\python.exe -m ml.evaluate --split test
  ```
  *(Pass `--no-pretrained` if running offline without cached ImageNet weights.)*

### 3. Run Backend & Frontend
Set `ADMIN_TOKEN` if you want to allow deleting history records (optional env vars: `HOST`, `PORT`, `FLASK_DEBUG`, `CORS_ORIGINS`, `DATABASE_URL`).

**Windows (PowerShell):**
```powershell
# Terminal 1 (Backend)
$env:ADMIN_TOKEN = "change-me"
.\backend\venv\Scripts\python.exe -m backend.app

# Terminal 2 (Frontend)
cd frontend
npm install
npm run dev
```
*(Or double-click `start_app.bat` on Windows.)*

### 4. Run Automated Tests (Isolated)
Tests use an in-memory SQLite database and temporary directories, leaving your local DB, uploads, and `ml/` directories untouched:
```powershell
.\backend\venv\Scripts\pytest.exe -v backend\tests\test_app_and_ml.py
```

---

## Veterinary Disclaimer
This application is for academic and preliminary screening purposes only. **Foot-and-Mouth Disease (FMD)** and **Lumpy Skin Disease (LSD)** are notifiable livestock diseases — always report suspected cases promptly to local veterinary authorities and consult a qualified veterinarian before taking treatment or herd-management actions.
