import json
import os
from flask import Blueprint, current_app, jsonify, request
from database.db import db
from models.db_models import Animal, Disease, Prediction
from services.prediction_service import predict_disease_from_image
from services.upload_service import validate_and_save_image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_ARCH_PATH = os.path.join(PROJECT_ROOT, "ml", "saved_models", "model_architecture.json")
TRAINING_HISTORY_PATH = os.path.join(PROJECT_ROOT, "ml", "saved_models", "training_history.json")
EVALUATION_METRICS_PATH = os.path.join(PROJECT_ROOT, "ml", "saved_models", "evaluation_metrics.json")

api_bp = Blueprint("api", __name__, url_prefix="/api")

AI_SUPPORTED_ANIMALS = {"cow", "buffalo"}
ALL_ANIMALS = {"cow", "buffalo", "goat", "sheep", "dog", "cat"}

INITIAL_ANIMALS = [
    {
        "slug": "cow",
        "name": "Cow",
        "emoji": "🐄",
        "ai_supported": True,
        "badge": "AI Image + Symptom Detection Available",
        "details": "Full support for MobileNetV2 image classification and rule-based symptom analysis."
    },
    {
        "slug": "buffalo",
        "name": "Buffalo",
        "emoji": "🐃",
        "ai_supported": True,
        "badge": "AI Image + Symptom Detection Available",
        "details": "Full support for MobileNetV2 image classification and rule-based symptom analysis."
    },
    {
        "slug": "goat",
        "name": "Goat",
        "emoji": "🐐",
        "ai_supported": False,
        "badge": "AI Image Detection Unavailable",
        "details": "AI image detection is disabled until a verified goat disease image dataset is trained."
    },
    {
        "slug": "sheep",
        "name": "Sheep",
        "emoji": "🐑",
        "ai_supported": False,
        "badge": "AI Image Detection Unavailable",
        "details": "AI image detection is disabled until a verified sheep disease image dataset is trained."
    },
    {
        "slug": "dog",
        "name": "Dog",
        "emoji": "🐕",
        "ai_supported": False,
        "badge": "AI Image Detection Unavailable",
        "details": "AI image detection is disabled until a verified canine disease image dataset is trained."
    },
    {
        "slug": "cat",
        "name": "Cat",
        "emoji": "🐈",
        "ai_supported": False,
        "badge": "AI Image Detection Unavailable",
        "details": "AI image detection is disabled until a verified feline disease image dataset is trained."
    }
]

SYMPTOMS_DATA = [
    {
        "id": "fever",
        "label": "Fever (High body temperature)",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "loss_of_appetite",
        "label": "Loss of appetite (Reduced feed intake)",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "coughing",
        "label": "Coughing or respiratory distress",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "diarrhea",
        "label": "Diarrhea",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "skin_lesions",
        "label": "Skin lesions / sores / scabs",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "swelling",
        "label": "Swelling (limbs, brisket, or lymph nodes)",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "weakness",
        "label": "Weakness / lethargy",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "difficulty_walking",
        "label": "Difficulty walking / lameness",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "reduced_milk",
        "label": "Reduced milk production",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep"]
    },
    {
        "id": "skin_nodules",
        "label": "Firm round skin nodules (2–5 cm) on head, neck, or body",
        "category": "specific",
        "animals": ["cow", "buffalo"]
    },
    {
        "id": "mouth_hoof_blisters",
        "label": "Blisters / vesicles on tongue, gums, muzzle, or hooves",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep"]
    },
    {
        "id": "excessive_salivation",
        "label": "Excessive ropy salivation / drooling",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "nasal_ocular_discharge",
        "label": "Nasal and ocular (watery eye) discharge",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"]
    },
    {
        "id": "fur_hair_loss",
        "label": "Patchy hair/fur loss or frequent scratching",
        "category": "specific",
        "animals": ["dog", "cat"]
    }
]

INITIAL_DISEASES = [
    {
        "slug": "lsd",
        "name": "Lumpy Skin Disease (LSD)",
        "affected_animals": "Cow, Buffalo",
        "ai_supported": True,
        "symptoms": [
            "Firm, round skin nodules (2–5 cm) on the head, neck, limbs, and body",
            "High fever (often exceeding 40°C / 104°F)",
            "Swelling of superficial lymph nodes and limbs",
            "Loss of appetite and sharp drop in milk production",
            "Nasal and ocular discharge"
        ],
        "causes": "Caused by the Lumpy Skin Disease virus (Capripoxvirus), primarily spread by blood-feeding insect vectors such as mosquitoes, biting flies, and ticks.",
        "prevention": [
            "Isolate affected cattle immediately from the rest of the herd.",
            "Follow regional veterinary vaccination schedules against LSD.",
            "Practice vector control (clean drainage, insect repellents, regular shed hygiene).",
            "Disinfect premises and avoid sharing needles or equipment between animals."
        ]
    },
    {
        "slug": "fmd",
        "name": "Foot-and-Mouth Disease (FMD)",
        "affected_animals": "Cow, Buffalo (also affects cloven-hoofed animals like Goat and Sheep)",
        "ai_supported": True,
        "symptoms": [
            "High fever followed by blister-like vesicles on the tongue, gums, muzzle, and hooves",
            "Excessive ropy salivation and smacking of lips",
            "Lameness, reluctance to stand, or difficulty walking due to hoof lesions",
            "Severe loss of appetite and sudden reduction in milk yield"
        ],
        "causes": "Caused by an Aphthovirus (family Picornaviridae). Spreads rapidly through direct contact with infected animals, contaminated feed, footwear, or aerosols.",
        "prevention": [
            "Ensure routine FMD vaccination as recommended by local veterinary authorities.",
            "Strictly quarantine newly introduced or sick animals.",
            "Sanitize footbaths, sheds, and feeding troughs regularly.",
            "Restrict movement of livestock during suspected local outbreaks."
        ]
    },
    {
        "slug": "healthy",
        "name": "Healthy Animal Baseline",
        "affected_animals": "Cow, Buffalo",
        "ai_supported": True,
        "symptoms": [
            "Clear coat and skin free of nodules, scabs, or open sores",
            "Normal body temperature, alert posture, and steady gait",
            "Regular appetite, rumination, and consistent milk output"
        ],
        "causes": "Good nutrition, clean housing, regular vaccination, and routine veterinary care.",
        "prevention": [
            "Provide balanced fodder and clean drinking water daily.",
            "Maintain dry, well-ventilated shelters.",
            "Keep an updated vaccination and deworming calendar with a veterinarian."
        ]
    }
]


def seed_initial_data():
    """Populate the SQLite database with initial Animals and Diseases if empty."""
    if Animal.query.count() == 0:
        for item in INITIAL_ANIMALS:
            db.session.add(Animal(**item))
        db.session.commit()

    if Disease.query.count() == 0:
        for item in INITIAL_DISEASES:
            db.session.add(
                Disease(
                    slug=item["slug"],
                    name=item["name"],
                    affected_animals=item["affected_animals"],
                    ai_supported=item["ai_supported"],
                    symptoms_json=json.dumps(item["symptoms"]),
                    causes=item["causes"],
                    prevention_json=json.dumps(item["prevention"])
                )
            )
        db.session.commit()


@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "AnimalCare AI Backend",
        "database": "sqlite",
        "aiSupportedAnimals": sorted(list(AI_SUPPORTED_ANIMALS))
    })


@api_bp.route("/animals", methods=["GET"])
def get_animals():
    animals = Animal.query.order_by(Animal.id.asc()).all()
    return jsonify({"animals": [a.to_dict() for a in animals]})


@api_bp.route("/symptoms", methods=["GET"])
def get_symptoms():
    animal_filter = (request.args.get("animal") or "").strip().lower()
    if animal_filter and animal_filter in ALL_ANIMALS:
        filtered = [s for s in SYMPTOMS_DATA if animal_filter in s["animals"]]
        return jsonify({"animal": animal_filter, "symptoms": filtered})
    return jsonify({"symptoms": SYMPTOMS_DATA})


@api_bp.route("/symptoms/submit", methods=["POST"])
def submit_symptoms():
    data = request.get_json(silent=True) or {}
    animal_id = (data.get("animal") or "").strip().lower()
    if animal_id not in ALL_ANIMALS:
        return jsonify({"error": "Please select a valid animal category."}), 400

    symptoms = data.get("symptoms")
    if not isinstance(symptoms, list) or len(symptoms) == 0:
        return jsonify({"error": "Please select at least one observed symptom."}), 400

    cleaned_symptoms = [str(s).strip() for s in symptoms if str(s).strip()]
    if not cleaned_symptoms:
        return jsonify({"error": "Please select at least one valid symptom."}), 400

    valid_for_animal = {
        s["id"]: s["label"]
        for s in SYMPTOMS_DATA
        if animal_id in s["animals"]
    }
    valid_labels_for_animal = set(valid_for_animal.values())

    resolved_labels = []
    for item in cleaned_symptoms:
        if item in valid_for_animal:
            resolved_labels.append(valid_for_animal[item])
        elif item in valid_labels_for_animal:
            resolved_labels.append(item)
        else:
            return jsonify({
                "error": f"Symptom '{item}' is not applicable to {animal_id.capitalize()}."
            }), 400

    animal_name = animal_id.capitalize()
    summary = (
        f"Recorded {len(resolved_labels)} observed symptom(s) for {animal_name}. "
        "Full rule-based condition matching will evaluate these symptoms in Week 3."
    )

    return jsonify({
        "message": "Symptoms validated and received by backend.",
        "animalId": animal_id,
        "animal": animal_name,
        "selectedSymptoms": resolved_labels,
        "symptomCount": len(resolved_labels),
        "symptomAnalysis": summary
    }), 200


@api_bp.route("/diseases", methods=["GET"])
def get_diseases():
    diseases = Disease.query.order_by(Disease.id.asc()).all()
    return jsonify({"diseases": [d.to_dict() for d in diseases]})


@api_bp.route("/model/info", methods=["GET"])
def get_model_info():
    payload = {
        "model_name": "AnimalCare_MobileNetV2",
        "backbone": "MobileNetV2",
        "input_shape": [224, 224, 3],
        "num_classes": 3,
        "class_names": ["healthy", "lumpy_skin_disease", "foot_and_mouth_disease"]
    }
    if os.path.isfile(MODEL_ARCH_PATH):
        with open(MODEL_ARCH_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
    if os.path.isfile(TRAINING_HISTORY_PATH):
        with open(TRAINING_HISTORY_PATH, "r", encoding="utf-8") as f:
            payload["training_history"] = json.load(f)
    if os.path.isfile(EVALUATION_METRICS_PATH):
        with open(EVALUATION_METRICS_PATH, "r", encoding="utf-8") as f:
            payload["evaluation_metrics"] = json.load(f)
    return jsonify(payload)


@api_bp.route("/upload", methods=["POST"])
def upload_image():
    animal_id = (request.form.get("animal") or "cow").strip().lower()
    if animal_id not in AI_SUPPORTED_ANIMALS:
        return jsonify({
            "error": f"AI image detection is currently unavailable for '{animal_id}'. Only Cow and Buffalo are supported."
        }), 400

    image_file = request.files.get("image")
    upload_info, error_msg = validate_and_save_image(
        image_file,
        current_app.config["UPLOAD_FOLDER"]
    )
    if error_msg:
        return jsonify({"error": error_msg}), 400

    saved_file_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        upload_info["filename"]
    )
    prediction = predict_disease_from_image(saved_file_path, animal_id=animal_id)

    return jsonify({
        "message": "Image uploaded, validated, and classified with MobileNetV2.",
        "animal": animal_id,
        "upload": upload_info,
        "prediction": prediction
    }), 201


@api_bp.route("/predict/image", methods=["POST"])
def predict_image_endpoint():
    animal_id = (request.form.get("animal") or "cow").strip().lower()
    if animal_id not in AI_SUPPORTED_ANIMALS:
        return jsonify({
            "error": f"AI image detection is currently unavailable for '{animal_id}'. Only Cow and Buffalo are supported."
        }), 400

    image_file = request.files.get("image")
    upload_info, error_msg = validate_and_save_image(
        image_file,
        current_app.config["UPLOAD_FOLDER"]
    )
    if error_msg:
        return jsonify({"error": error_msg}), 400

    saved_file_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        upload_info["filename"]
    )
    prediction = predict_disease_from_image(saved_file_path, animal_id=animal_id)

    save_history_flag = (request.form.get("saveHistory") or "true").strip().lower() != "false"
    saved_record = None
    if save_history_flag:
        record = Prediction(
            animal=animal_id.capitalize(),
            image_path=upload_info["imagePath"],
            selected_symptoms_json=json.dumps([]),
            image_prediction=prediction["imagePrediction"],
            confidence=prediction["confidence"],
            symptom_analysis=prediction["summary"]
        )
        db.session.add(record)
        db.session.commit()
        saved_record = record.to_dict()

    return jsonify({
        "message": "MobileNetV2 image classification complete.",
        "animal": animal_id,
        "upload": upload_info,
        "prediction": prediction,
        "record": saved_record
    }), 200


@api_bp.route("/history", methods=["GET"])
def get_history():
    records = Prediction.query.order_by(Prediction.created_at.desc(), Prediction.id.desc()).all()
    return jsonify({"records": [r.to_dict() for r in records]})


@api_bp.route("/history", methods=["POST"])
@api_bp.route("/predictions", methods=["POST"])
def create_prediction_record():
    data = request.get_json(silent=True) or {}
    animal = (data.get("animal") or "").strip()
    if not animal:
        return jsonify({"error": "Animal category is required."}), 400

    symptoms = data.get("symptoms") or []
    if not isinstance(symptoms, list):
        symptoms = [str(symptoms)]

    confidence = data.get("confidence")
    if confidence is not None:
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = None

    record = Prediction(
        animal=animal,
        image_path=data.get("imagePath"),
        selected_symptoms_json=json.dumps(symptoms),
        image_prediction=data.get("imagePrediction") or "N/A",
        confidence=confidence,
        symptom_analysis=data.get("symptomAnalysis") or "N/A"
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"message": "Prediction record saved.", "record": record.to_dict()}), 201
