# AnimalCare AI – Animal Disease Detection System

A simple college-level web application for preliminary animal disease screening using image classification (MobileNetV2) and rule-based symptom analysis.

## Supported Animals
- **Working AI Image Detection:** Cow, Buffalo
- **Displayed (AI Image Detection Unavailable):** Goat, Sheep, Dog, Cat

## Technology Stack
- **Frontend:** React.js (Vite), JavaScript, HTML, CSS, Axios, React Router
- **Backend:** Python, Flask, Flask-CORS, SQLAlchemy, SQLite
- **AI/ML:** TensorFlow / Keras (MobileNetV2), OpenCV, NumPy, Scikit-learn

## Project Setup & Execution

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
The Flask server runs at `http://localhost:5000`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The React development server runs at `http://localhost:5173`.
