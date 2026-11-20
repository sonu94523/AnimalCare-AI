import hmac
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request

from backend.database.db import db
from backend.models.db_models import Animal, Disease, Prediction, UploadRecord
from backend.services.decision_service import evaluate_combined_decision
from backend.services.prediction_service import (
    ModelUnavailableError,
    is_model_available,
    predict_disease_from_image,
)
from backend.services.symptom_service import SYMPTOM_CATALOG, analyze_symptoms, resolve_symptom_ids
from backend.services.upload_service import delete_uploaded_file, validate_and_save_image
from ml.constants import (
    ARCHITECTURE_FILENAME,
    EVALUATION_METRICS_FILENAME,
    MODEL_STATUS_NOTE,
    TRAINING_HISTORY_FILENAME,
)

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")

AI_SUPPORTED_ANIMALS = {"cow", "buffalo"}
ALL_ANIMALS = {"cow", "buffalo", "goat", "sheep", "dog", "cat"}

INITIAL_ANIMALS = [
    {
        "slug": "cow",
        "name": "Cow",
        "emoji": "🐄",
        "ai_supported": True,
        "badge": "Demo Image + Symptom Screening",
        "details": "Supports MobileNetV2 demo image screening (not clinically validated) and rule-based symptom analysis.",
    },
    {
        "slug": "buffalo",
        "name": "Buffalo",
        "emoji": "🐃",
        "ai_supported": True,
        "badge": "Demo Image + Symptom Screening",
        "details": "Supports MobileNetV2 demo image screening (not clinically validated) and rule-based symptom analysis.",
    },
    {
        "slug": "goat",
        "name": "Goat",
        "emoji": "🐐",
        "ai_supported": False,
        "badge": "AI Image Detection Unavailable",
        "details": "AI image detection is disabled until a verified goat disease image dataset is trained.",
    },
    {
        "slug": "sheep",
        "name": "Sheep",
        "emoji": "🐑",
        "ai_supported": False,
        "badge": "AI Image Detection Unavailable",
        "details": "AI image detection is disabled until a verified sheep disease image dataset is trained.",
    },
    {
        "slug": "dog",
        "name": "Dog",
        "emoji": "🐕",
        "ai_supported": False,
        "badge": "AI Image Detection Unavailable",
        "details": "AI image detection is disabled until a verified canine disease image dataset is trained.",
    },
    {
        "slug": "cat",
        "name": "Cat",
        "emoji": "🐈",
        "ai_supported": False,
        "badge": "AI Image Detection Unavailable",
        "details": "AI image detection is disabled until a verified feline disease image dataset is trained.",
    },
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
            "Nasal and ocular discharge",
        ],
        "causes": "Caused by the Lumpy Skin Disease virus (Capripoxvirus), primarily spread by blood-feeding insect vectors such as mosquitoes, biting flies, and ticks.",
        "prevention": [
            "Isolate affected cattle immediately from the rest of the herd.",
            "Report suspected cases to local veterinary authorities (LSD is a notifiable livestock disease).",
            "Follow regional veterinary vaccination schedules against LSD.",
            "Practice vector control (clean drainage, insect repellents, regular shed hygiene).",
        ],
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
            "Severe loss of appetite and sudden reduction in milk yield",
        ],
        "causes": "Caused by an Aphthovirus (family Picornaviridae). Spreads rapidly through direct contact with infected animals, contaminated feed, footwear, or aerosols.",
        "prevention": [
            "Report suspected cases immediately to local veterinary authorities (FMD is a WOAH-listed notifiable disease).",
            "Ensure routine FMD vaccination as recommended by local veterinary authorities.",
            "Strictly quarantine newly introduced or sick animals.",
            "Sanitize footbaths, sheds, and feeding troughs regularly.",
        ],
    },
    {
        "slug": "healthy",
        "name": "Healthy Animal Baseline",
        "affected_animals": "Cow, Buffalo",
        "ai_supported": True,
        "symptoms": [
            "Clear coat and skin free of nodules, scabs, or open sores",
            "Normal body temperature, alert posture, and steady gait",
            "Regular appetite, rumination, and consistent milk output",
        ],
        "causes": "Good nutrition, clean housing, regular vaccination, and routine veterinary care.",
        "prevention": [
            "Provide balanced fodder and clean drinking water daily.",
            "Maintain dry, well-ventilated shelters.",
            "Keep an updated vaccination and deworming calendar with a veterinarian.",
        ],
    },
]


def seed_initial_data() -> None:
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
                    prevention_json=json.dumps(item["prevention"]),
                )
            )
        db.session.commit()


def _parse_json_object() -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[Any, int]]]:
    """Parse a JSON request body and ensure it is a JSON object (dict)."""
    if not request.is_json:
        return {}, None
    parsed = request.get_json(silent=True)
    if parsed is None:
        return None, (jsonify({"error": "Malformed JSON request body."}), 400)
    if not isinstance(parsed, dict):
        return None, (jsonify({"error": "Request body must be a JSON object."}), 400)
    return parsed, None


def _require_admin_token() -> Optional[Tuple[Any, int]]:
    """Fail-closed admin token guard for destructive or manual history writes."""
    expected = (current_app.config.get("ADMIN_TOKEN") or "").strip()
    if not expected:
        return jsonify({
            "error": "Admin actions are disabled until ADMIN_TOKEN is configured on the server."
        }), 403

    provided = (request.headers.get("X-Admin-Token") or "").strip()
    if not provided:
        auth_header = (request.headers.get("Authorization") or "").strip()
        if auth_header.lower().startswith("bearer "):
            provided = auth_header[7:].strip()

    if not provided or not hmac.compare_digest(provided, expected):
        return jsonify({"error": "Unauthorized. Provide a valid X-Admin-Token header."}), 401
    return None


def _parse_save_history_flag(data: Dict[str, Any]) -> bool:
    if "saveHistory" in data:
        return data.get("saveHistory") is not False
    form_val = request.form.get("saveHistory")
    if form_val is not None:
        return form_val.strip().lower() != "false"
    return True


def _run_image_upload_and_predict(animal_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[Any, int]]]:
    """Validate upload, run MobileNetV2 inference, and store a server-side UploadRecord."""
    if animal_id not in AI_SUPPORTED_ANIMALS:
        return None, (jsonify({
            "error": f"AI image detection is currently unavailable for '{animal_id}'. Only Cow and Buffalo are supported."
        }), 400)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    image_file = request.files.get("image")
    upload_info, error_msg = validate_and_save_image(image_file, upload_folder)
    if error_msg:
        return None, (jsonify({"error": error_msg}), 400)

    saved_file_path = os.path.join(upload_folder, upload_info["filename"])
    try:
        prediction = predict_disease_from_image(
            saved_file_path,
            animal_id=animal_id,
            models_dir=current_app.config["MODELS_DIR"],
            dataset_dir=current_app.config["DATASET_DIR"],
        )
    except ModelUnavailableError as exc:
        delete_uploaded_file(upload_folder, upload_info["imagePath"])
        logger.warning("Image prediction unavailable (503): %s", exc)
        return None, (jsonify({"error": str(exc)}), 503)

    upload_id = uuid.uuid4().hex
    upload_record = UploadRecord(
        id=upload_id,
        animal=animal_id,
        filename=upload_info["filename"],
        original_name=upload_info["originalName"],
        image_path=upload_info["imagePath"],
        prediction_json=json.dumps(prediction),
    )
    db.session.add(upload_record)
    db.session.commit()

    upload_info_with_id = {**upload_info, "uploadId": upload_id}
    return {"upload": upload_info_with_id, "prediction": prediction}, None


@api_bp.route("/health", methods=["GET"])
def health_check():
    models_dir = current_app.config["MODELS_DIR"]
    return jsonify({
        "status": "ok",
        "service": "AnimalCare AI Backend",
        "database": "sqlite",
        "aiSupportedAnimals": sorted(list(AI_SUPPORTED_ANIMALS)),
        "modelLoaded": is_model_available(models_dir),
        "modelValidated": False,
    })


@api_bp.route("/animals", methods=["GET"])
def get_animals():
    animals = Animal.query.order_by(Animal.id.asc()).all()
    return jsonify({"animals": [a.to_dict() for a in animals]})


@api_bp.route("/symptoms", methods=["GET"])
def get_symptoms():
    animal_filter = (request.args.get("animal") or "").strip().lower()
    if animal_filter and animal_filter in ALL_ANIMALS:
        filtered = [s for s in SYMPTOM_CATALOG if animal_filter in s["animals"]]
        return jsonify({"animal": animal_filter, "symptoms": filtered})
    return jsonify({"symptoms": SYMPTOM_CATALOG})


@api_bp.route("/symptoms/submit", methods=["POST"])
def submit_symptoms():
    data, err_resp = _parse_json_object()
    if err_resp:
        return err_resp

    animal_id = str(data.get("animal") or "").strip().lower()
    if animal_id not in ALL_ANIMALS:
        return jsonify({"error": "Please select a valid animal category."}), 400

    symptoms = data.get("symptoms")
    if not isinstance(symptoms, list) or len(symptoms) == 0:
        return jsonify({"error": "Please select at least one observed symptom."}), 400

    resolved_ids, resolved_labels, err_msg = resolve_symptom_ids(animal_id, symptoms)
    if err_msg:
        return jsonify({"error": err_msg}), 400

    analysis = analyze_symptoms(animal_id, resolved_ids)
    combined_decision = evaluate_combined_decision(
        animal_id=animal_id,
        image_result=None,
        symptom_result=analysis,
    )

    saved_record = None
    if _parse_save_history_flag(data):
        image_pred_text = (
            "No image uploaded (Symptom-only check)"
            if animal_id in AI_SUPPORTED_ANIMALS
            else f"AI Image Detection unavailable for {analysis['animal']}"
        )
        record = Prediction(
            animal=analysis["animal"],
            image_path=None,
            selected_symptoms_json=json.dumps(resolved_labels),
            image_prediction=image_pred_text,
            confidence=analysis["matchScorePercent"],
            symptom_analysis=f"{analysis['topCondition']} ({analysis['matchLevel']} - {analysis['matchScorePercent']}%)",
        )
        db.session.add(record)
        db.session.commit()
        saved_record = record.to_dict()

    return jsonify({
        "message": "Symptom rule analysis completed.",
        **analysis,
        "combinedDecision": combined_decision,
        "record": saved_record,
    }), 200


@api_bp.route("/diseases", methods=["GET"])
def get_diseases():
    diseases = Disease.query.order_by(Disease.id.asc()).all()
    return jsonify({"diseases": [d.to_dict() for d in diseases]})


@api_bp.route("/model/info", methods=["GET"])
def get_model_info():
    models_dir = current_app.config["MODELS_DIR"]
    payload: Dict[str, Any] = {
        "modelName": "AnimalCare_MobileNetV2",
        "backbone": "MobileNetV2",
        "framework": "pytorch",
        "inputShape": [224, 224, 3],
        "numClasses": 3,
        "classNames": ["healthy", "lumpy_skin_disease", "foot_and_mouth_disease"],
        "modelLoaded": is_model_available(models_dir),
        "validated": False,
        "statusNote": MODEL_STATUS_NOTE,
    }

    arch_path = os.path.join(models_dir, ARCHITECTURE_FILENAME)
    if os.path.isfile(arch_path):
        try:
            with open(arch_path, "r", encoding="utf-8") as f:
                payload.update(json.load(f))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read %s: %s", arch_path, exc)

    hist_path = os.path.join(models_dir, TRAINING_HISTORY_FILENAME)
    if os.path.isfile(hist_path):
        try:
            with open(hist_path, "r", encoding="utf-8") as f:
                payload["trainingHistory"] = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read %s: %s", hist_path, exc)

    eval_path = os.path.join(models_dir, EVALUATION_METRICS_FILENAME)
    if os.path.isfile(eval_path):
        try:
            with open(eval_path, "r", encoding="utf-8") as f:
                payload["evaluationMetrics"] = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read %s: %s", eval_path, exc)

    payload["modelLoaded"] = is_model_available(models_dir)
    payload["validated"] = False
    payload["statusNote"] = MODEL_STATUS_NOTE
    return jsonify(payload)


@api_bp.route("/upload", methods=["POST"])
def upload_image():
    """Upload, validate and classify an image without creating a history row yet.

    Returns a server-side `uploadId` that can later be passed to `/api/predict/combined`.
    """
    animal_id = (request.form.get("animal") or "cow").strip().lower()
    result, err_resp = _run_image_upload_and_predict(animal_id)
    if err_resp:
        return err_resp

    return jsonify({
        "message": "Image uploaded, validated, and classified with the MobileNetV2 demo model.",
        "animalId": animal_id,
        "animal": animal_id.capitalize(),
        "uploadId": result["upload"]["uploadId"],
        "upload": result["upload"],
        "prediction": result["prediction"],
    }), 201


@api_bp.route("/predict/image", methods=["POST"])
def predict_image_endpoint():
    animal_id = (request.form.get("animal") or "cow").strip().lower()
    result, err_resp = _run_image_upload_and_predict(animal_id)
    if err_resp:
        return err_resp

    upload_info = result["upload"]
    prediction = result["prediction"]
    combined_decision = evaluate_combined_decision(
        animal_id=animal_id,
        image_result=prediction,
        symptom_result=None,
    )

    saved_record = None
    if _parse_save_history_flag({}):
        record = Prediction(
            animal=animal_id.capitalize(),
            image_path=upload_info["imagePath"],
            selected_symptoms_json=json.dumps([]),
            image_prediction=prediction["imagePrediction"],
            confidence=prediction["confidence"],
            symptom_analysis=prediction["summary"],
        )
        db.session.add(record)
        db.session.commit()
        saved_record = record.to_dict()

    return jsonify({
        "message": "MobileNetV2 demo image classification complete.",
        "animalId": animal_id,
        "animal": animal_id.capitalize(),
        "uploadId": upload_info["uploadId"],
        "upload": upload_info,
        "prediction": prediction,
        "combinedDecision": combined_decision,
        "record": saved_record,
    }), 200


@api_bp.route("/predict/combined", methods=["POST"])
def predict_combined_endpoint():
    data, err_resp = _parse_json_object()
    if err_resp:
        return err_resp

    animal_id = str(data.get("animal") or request.form.get("animal") or "cow").strip().lower()
    if animal_id not in ALL_ANIMALS:
        return jsonify({"error": "Please select a valid animal category."}), 400

    # Reject attempts to supply client-forged predictions or arbitrary external paths.
    if "imagePredictionData" in data or "imagePath" in data:
        return jsonify({
            "error": "Client-supplied imagePredictionData and imagePath are not accepted. "
                     "Upload an image file or pass the server-issued uploadId."
        }), 400

    # 1. Resolve image prediction strictly from server-side upload or fresh file
    image_result = None
    image_path = None
    upload_id = data.get("uploadId") or request.form.get("uploadId")

    if "image" in request.files:
        result, upload_err = _run_image_upload_and_predict(animal_id)
        if upload_err:
            return upload_err
        image_result = result["prediction"]
        image_path = result["upload"]["imagePath"]
    elif upload_id is not None:
        if not isinstance(upload_id, str) or not upload_id.strip():
            return jsonify({"error": "Invalid uploadId."}), 400
        upload_rec = db.session.get(UploadRecord, upload_id.strip())
        if not upload_rec:
            return jsonify({"error": "Upload record not found for the given uploadId."}), 404
        if upload_rec.animal != animal_id:
            return jsonify({
                "error": f"Upload record belongs to '{upload_rec.animal}', not '{animal_id}'."
            }), 400
        image_result = json.loads(upload_rec.prediction_json)
        image_path = upload_rec.image_path

    # 2. Resolve symptom analysis
    raw_symptoms = data.get("symptoms")
    if raw_symptoms is None and request.form.get("symptoms"):
        form_sym = request.form.get("symptoms", "")
        try:
            raw_symptoms = json.loads(form_sym)
        except json.JSONDecodeError:
            raw_symptoms = [s.strip() for s in form_sym.split(",") if s.strip()]

    symptom_result = None
    resolved_labels = []
    if raw_symptoms is not None:
        if not isinstance(raw_symptoms, list):
            return jsonify({"error": "Field 'symptoms' must be a list."}), 400
        if len(raw_symptoms) > 0:
            resolved_ids, resolved_labels, err_msg = resolve_symptom_ids(animal_id, raw_symptoms)
            if err_msg:
                return jsonify({"error": err_msg}), 400
            symptom_result = analyze_symptoms(animal_id, resolved_ids)

    if not image_result and not symptom_result:
        return jsonify({
            "error": "Please provide an uploaded image (or uploadId), observed symptoms, or both."
        }), 400

    combined_decision = evaluate_combined_decision(
        animal_id=animal_id,
        image_result=image_result,
        symptom_result=symptom_result,
    )

    saved_record = None
    if _parse_save_history_flag(data):
        img_pred_str = (
            (image_result.get("imagePrediction") or image_result.get("predictedLabel") or "N/A")
            if image_result
            else (
                "No image uploaded (Symptom-only check)"
                if animal_id in AI_SUPPORTED_ANIMALS
                else f"AI Image Detection unavailable for {animal_id.capitalize()}"
            )
        )
        sym_summary_str = (
            f"{symptom_result['topCondition']} ({symptom_result['matchScorePercent']}%) — {combined_decision['agreementStatus']}"
            if symptom_result
            else combined_decision["explanation"]
        )
        record = Prediction(
            animal=animal_id.capitalize(),
            image_path=image_path,
            selected_symptoms_json=json.dumps(resolved_labels),
            image_prediction=img_pred_str,
            confidence=combined_decision["combinedConfidence"],
            symptom_analysis=sym_summary_str,
        )
        db.session.add(record)
        db.session.commit()
        saved_record = record.to_dict()

    return jsonify({
        "message": "Combined image and symptom decision completed.",
        "animalId": animal_id,
        "animal": animal_id.capitalize(),
        "imageResult": image_result,
        "symptomResult": symptom_result,
        "combinedDecision": combined_decision,
        "record": saved_record,
    }), 200


@api_bp.route("/history", methods=["GET"])
def get_history():
    animal_filter = (request.args.get("animal") or "").strip().lower()
    query = Prediction.query
    if animal_filter and animal_filter != "all":
        query = query.filter(db.func.lower(Prediction.animal) == animal_filter)

    records = query.order_by(Prediction.created_at.desc(), Prediction.id.desc()).all()
    return jsonify({
        "totalCount": len(records),
        "records": [r.to_dict() for r in records],
    })


@api_bp.route("/history/<int:record_id>", methods=["GET"])
def get_history_record(record_id: int):
    record = db.session.get(Prediction, record_id)
    if not record:
        return jsonify({"error": "Prediction record not found."}), 404
    return jsonify({"record": record.to_dict()}), 200


@api_bp.route("/history/<int:record_id>", methods=["DELETE"])
def delete_history_record(record_id: int):
    auth_err = _require_admin_token()
    if auth_err:
        return auth_err

    record = db.session.get(Prediction, record_id)
    if not record:
        return jsonify({"error": "Prediction record not found."}), 404

    img_path = record.image_path
    db.session.delete(record)
    db.session.commit()

    # Remove the image file if no other Prediction row still references it.
    if img_path and Prediction.query.filter_by(image_path=img_path).count() == 0:
        delete_uploaded_file(current_app.config["UPLOAD_FOLDER"], img_path)
        UploadRecord.query.filter_by(image_path=img_path).delete()
        db.session.commit()

    return jsonify({"message": f"Prediction record #{record_id} deleted.", "deletedId": record_id}), 200


@api_bp.route("/history", methods=["DELETE"])
def clear_all_history():
    auth_err = _require_admin_token()
    if auth_err:
        return auth_err

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    all_records = Prediction.query.all()
    image_paths = {r.image_path for r in all_records if r.image_path}
    deleted_count = Prediction.query.delete()
    UploadRecord.query.delete()
    db.session.commit()

    for img_path in image_paths:
        delete_uploaded_file(upload_folder, img_path)

    return jsonify({"message": "All prediction history records cleared.", "deletedCount": deleted_count}), 200
