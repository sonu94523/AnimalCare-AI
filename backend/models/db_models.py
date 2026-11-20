import json
from datetime import datetime, timezone
from backend.database.db import db


class Animal(db.Model):
    __tablename__ = "animals"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    emoji = db.Column(db.String(16), nullable=False)
    ai_supported = db.Column(db.Boolean, default=False, nullable=False)
    badge = db.Column(db.String(128), nullable=False)
    details = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.slug,
            "name": self.name,
            "emoji": self.emoji,
            "aiSupported": self.ai_supported,
            "badge": self.badge,
            "details": self.details,
        }


class Disease(db.Model):
    __tablename__ = "diseases"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    affected_animals = db.Column(db.String(128), nullable=False)
    ai_supported = db.Column(db.Boolean, default=True, nullable=False)
    symptoms_json = db.Column(db.Text, nullable=False)
    causes = db.Column(db.Text, nullable=False)
    prevention_json = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.slug,
            "name": self.name,
            "affectedAnimals": self.affected_animals,
            "aiSupported": self.ai_supported,
            "symptoms": json.loads(self.symptoms_json) if self.symptoms_json else [],
            "causes": self.causes,
            "prevention": json.loads(self.prevention_json) if self.prevention_json else [],
        }


class UploadRecord(db.Model):
    """Server-side store of validated uploads and their server-computed model output.

    Combined screening looks up predictions by `id` here rather than accepting
    image predictions or paths from the client request body.
    """

    __tablename__ = "uploads"

    id = db.Column(db.String(32), primary_key=True)
    animal = db.Column(db.String(32), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256), nullable=False)
    image_path = db.Column(db.String(256), nullable=False)
    prediction_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "uploadId": self.id,
            "animal": self.animal,
            "filename": self.filename,
            "originalName": self.original_name,
            "imagePath": self.image_path,
            "prediction": json.loads(self.prediction_json),
        }


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    animal = db.Column(db.String(64), nullable=False)
    image_path = db.Column(db.String(256), nullable=True)
    selected_symptoms_json = db.Column(db.Text, nullable=True)
    image_prediction = db.Column(db.String(128), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    symptom_analysis = db.Column(db.Text, nullable=True)
    details_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        details = json.loads(self.details_json) if self.details_json else None
        return {
            "id": self.id,
            "animal": self.animal,
            "animalId": (self.animal or "").strip().lower(),
            "imagePath": self.image_path,
            "symptoms": json.loads(self.selected_symptoms_json) if self.selected_symptoms_json else [],
            "imagePrediction": self.image_prediction or "N/A",
            "confidence": self.confidence,
            "symptomAnalysis": self.symptom_analysis or "N/A",
            "details": details,
            "date": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }
