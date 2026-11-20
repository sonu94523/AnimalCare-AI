# AnimalCare AI – Animal Disease Detection System

A simple, transparent web application for preliminary animal disease screening using **MobileNetV2 transfer learning** (`224 × 224` RGB image classification), a **weighted rule-based clinical symptom analysis engine**, and an **honest combined decision & uncertainty handler**.

---

## Key Features
- **6 Animal Categories Displayed:**
  - **Working AI Image + Symptom Detection:** **Cow**, **Buffalo**
  - **Symptom Reference Only (AI Image Detection Unavailable):** **Goat**, **Sheep**, **Dog**, **Cat** (explicitly labeled so the system never generates fake image predictions for unsupported animals)
- **MobileNetV2 Image Screening (`ml/`):**
  - Preprocesses uploaded JPG/JPEG/PNG photos (`max 5 MB`) to `224 × 224` RGB tensors normalized to `[-1.0, 1.0]`.
  - Classifies Cow and Buffalo images into:
    1. **Healthy** (`healthy`)
    2. **Lumpy Skin Disease (LSD)** (`lumpy_skin_disease`)
    3. **Foot-and-Mouth Disease (FMD)** (`foot_and_mouth_disease`)
  - Flags predictions below the `60.0%` confidence threshold as **Uncertain / Low Confidence**.
- **Rule-Based Symptom Checker (`backend/services/symptom_service.py`):**
  - Evaluates general and animal-specific clinical signs using weighted hallmark and supporting symptom rules.
  - Prevents single non-specific signs (such as fever alone) from overclaiming a specific disease diagnosis.
- **Combined Image + Symptom Decision Engine (`backend/services/decision_service.py`):**
  - Cross-checks MobileNetV2 visual predictions against reported clinical symptoms.
  - Reports **Agreement**, **Conflict / Disagreement Detected**, or **Partial / Low-Confidence Evidence**.
- **SQLite Prediction History & Disease Reference (`backend/models/db_models.py`):**
  - Stores screening records in SQLite with animal filtering, detailed view, and record deletion.

---

## Project Architecture
```text
AnimalCare-AI/
├── backend/
│   ├── app.py                        # Flask application entry point & CORS setup
│   ├── requirements.txt              # Python backend & ML dependencies
│   ├── database/
│   │   └── db.py                     # SQLite & SQLAlchemy configuration
│   ├── models/
│   │   └── db_models.py              # Animal, Disease, and Prediction tables
│   ├── routes/
│   │   └── api_routes.py             # REST API endpoints (/api/*)
│   ├── services/
│   │   ├── upload_service.py         # Image validation, saving & 224x224 preprocessing check
│   │   ├── prediction_service.py     # MobileNetV2 image inference & confidence thresholding
│   │   ├── symptom_service.py        # Weighted rule-based symptom matching engine
│   │   └── decision_service.py       # Combined image + symptom agreement/conflict engine
│   └── tests/
│       └── test_app_and_ml.py        # Automated end-to-end API & ML test suite
├── frontend/
│   ├── package.json                  # React 18, Vite, React Router, Axios
│   └── src/
│       ├── App.jsx                   # Application routes & layout
│       ├── components/               # Navbar & Footer
│       ├── pages/                    # Home, AnimalSelection, ImageDetection, SymptomChecker, Results, DiseaseInfo, History
│       └── services/
│           └── api.js                # Axios REST API client
└── ml/
    ├── preprocessing.py              # Dataset organization, 224x224 RGB preprocessing & augmentation
    ├── model.py                      # MobileNetV2 transfer learning architecture & checkpointing
    ├── train.py                      # Training loop & training_history.json generation
    ├── evaluate.py                   # Test-split evaluation, confusion matrix & F1 metrics
    ├── dataset/                      # Train (70%), Val (15%), Test (15%) dataset splits
    └── saved_models/                 # Saved architecture, training history, evaluation metrics & weights
```

---

## REST API Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Backend health check & AI-supported animal list |
| `GET` | `/api/animals` | List all 6 animal categories and AI support status |
| `GET` | `/api/symptoms` | List clinical symptoms (supports `?animal=cow` filter) |
| `POST` | `/api/symptoms/submit` | Run rule-based symptom analysis and save screening record |
| `GET` | `/api/diseases` | List reference information for supported conditions |
| `POST` | `/api/upload` | Validate, preprocess, and classify an uploaded Cow/Buffalo image |
| `POST` | `/api/predict/image` | Run MobileNetV2 image inference and save to SQLite history |
| `POST` | `/api/predict/combined` | Run combined MobileNetV2 image + symptom decision engine |
| `GET` | `/api/model/info` | Inspect MobileNetV2 architecture, training history & evaluation metrics |
| `GET` | `/api/history` | List saved prediction history (supports `?animal=cow` filter) |
| `DELETE` | `/api/history/<id>` | Delete a specific prediction history record |
| `DELETE` | `/api/history` | Clear all prediction history records |

---

## Setup & Execution

### 1. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
The Flask server runs at **`http://localhost:5000`**.

### 2. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
The React development server runs at **`http://localhost:5173`**.

### 3. ML Pipeline & Automated Tests
```powershell
# Initialize dataset splits & verify preprocessing
python ml/preprocessing.py --init --seed-samples --verify

# Train MobileNetV2 model & save checkpoint
python ml/train.py --epochs 8

# Evaluate model on test split & generate confusion matrix
python ml/evaluate.py

# Run automated backend & ML test suite
.\backend\venv\Scripts\python.exe backend\tests\test_app_and_ml.py
```

---

## Veterinary Disclaimer
This system is built for academic and preliminary screening purposes only. It does **not** provide a confirmed veterinary diagnosis or prescribe medication dosages. Always consult a qualified veterinarian for examination and treatment.
