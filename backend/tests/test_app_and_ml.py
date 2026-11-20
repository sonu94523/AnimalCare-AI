"""
Automated Unit & Integration Test Suite for AnimalCare AI.

Covers:
1. Flask REST API endpoints (/api/health, /api/animals, /api/diseases, /api/symptoms, /api/model/info)
2. MobileNetV2 image preprocessing (224x224 RGB, [-1, 1] normalization) and inference
3. Image upload validation (supported animals Cow/Buffalo vs. unsupported animals, file format checks)
4. Rule-based symptom analysis engine (LSD, FMD, and non-specific symptom handling)
5. Combined image + symptom decision engine (agreement, conflict/disagreement, and uncertainty)
6. SQLite prediction history persistence, animal filtering, and record deletion
"""

import io
import json
import os
import sys
import unittest
from PIL import Image

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TESTS_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

for path in (PROJECT_ROOT, BACKEND_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

_BASE_SITE_PACKAGES = os.path.join(getattr(sys, "base_prefix", sys.prefix), "Lib", "site-packages")
if os.path.isdir(_BASE_SITE_PACKAGES) and _BASE_SITE_PACKAGES not in sys.path:
    sys.path.append(_BASE_SITE_PACKAGES)

from backend.app import create_app
from backend.services.decision_service import evaluate_combined_decision
from backend.services.symptom_service import analyze_symptoms, resolve_symptom_ids
from ml.preprocessing import IMAGE_SHAPE, preprocess_image


def _create_test_jpeg_bytes(color=(160, 110, 85), size=(300, 240)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color)
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


class AnimalCareAITestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_health_and_animals_endpoints(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(sorted(data["aiSupportedAnimals"]), ["buffalo", "cow"])

        animals_resp = self.client.get("/api/animals")
        self.assertEqual(animals_resp.status_code, 200)
        animals = animals_resp.get_json()["animals"]
        self.assertEqual(len(animals), 6)
        supported_ids = {a["id"] for a in animals if a["aiSupported"]}
        unsupported_ids = {a["id"] for a in animals if not a["aiSupported"]}
        self.assertEqual(supported_ids, {"cow", "buffalo"})
        self.assertEqual(unsupported_ids, {"goat", "sheep", "dog", "cat"})

    def test_02_diseases_and_model_info_endpoints(self):
        diseases_resp = self.client.get("/api/diseases")
        self.assertEqual(diseases_resp.status_code, 200)
        diseases = diseases_resp.get_json()["diseases"]
        self.assertGreaterEqual(len(diseases), 3)

        model_resp = self.client.get("/api/model/info")
        self.assertEqual(model_resp.status_code, 200)
        model_info = model_resp.get_json()
        self.assertEqual(model_info["backbone"], "MobileNetV2")
        self.assertEqual(model_info["input_shape"], [224, 224, 3])
        self.assertEqual(model_info["num_classes"], 3)

    def test_03_image_preprocessing_pipeline(self):
        raw_bytes = _create_test_jpeg_bytes()
        tensor = preprocess_image(raw_bytes, expand_dims=True)
        self.assertEqual(tensor.shape, (1, *IMAGE_SHAPE))
        self.assertGreaterEqual(float(tensor.min()), -1.001)
        self.assertLessEqual(float(tensor.max()), 1.001)

    def test_04_image_upload_and_prediction_validation(self):
        # Valid Cow image prediction
        jpeg_bytes = _create_test_jpeg_bytes()
        resp = self.client.post(
            "/api/predict/image",
            data={
                "animal": "cow",
                "image": (io.BytesIO(jpeg_bytes), "test_cow.jpg"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertIn("prediction", payload)
        self.assertEqual(payload["prediction"]["inputShape"], [1, 224, 224, 3])
        self.assertEqual(len(payload["prediction"]["classProbabilities"]), 3)

        # Unsupported animal for AI image detection (Goat) must return 400
        unsupported_resp = self.client.post(
            "/api/predict/image",
            data={
                "animal": "goat",
                "image": (io.BytesIO(jpeg_bytes), "test_goat.jpg"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(unsupported_resp.status_code, 400)

        # Invalid file format (.txt) must return 400
        invalid_file_resp = self.client.post(
            "/api/predict/image",
            data={
                "animal": "cow",
                "image": (io.BytesIO(b"not an image"), "notes.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(invalid_file_resp.status_code, 400)

    def test_05_symptom_rule_engine_and_endpoint(self):
        # LSD symptom match for Cow
        lsd_resp = self.client.post(
            "/api/symptoms/submit",
            json={
                "animal": "cow",
                "symptoms": ["skin_nodules", "fever", "swelling", "reduced_milk"],
            },
        )
        self.assertEqual(lsd_resp.status_code, 200)
        lsd_data = lsd_resp.get_json()
        self.assertEqual(lsd_data["topConditionId"], "lumpy_skin_disease")
        self.assertGreaterEqual(lsd_data["matchScorePercent"], 60.0)

        # FMD symptom match for Buffalo
        fmd_resp = self.client.post(
            "/api/symptoms/submit",
            json={
                "animal": "buffalo",
                "symptoms": ["mouth_hoof_blisters", "excessive_salivation", "difficulty_walking"],
            },
        )
        self.assertEqual(fmd_resp.status_code, 200)
        fmd_data = fmd_resp.get_json()
        self.assertEqual(fmd_data["topConditionId"], "foot_and_mouth_disease")
        self.assertGreaterEqual(fmd_data["matchScorePercent"], 60.0)

        # Non-specific single symptom on Dog
        dog_ids, _, err = resolve_symptom_ids("dog", ["fever"])
        self.assertEqual(err, "")
        dog_analysis = analyze_symptoms("dog", dog_ids)
        self.assertEqual(dog_analysis["topConditionId"], "inconclusive")

        # Inapplicable symptom for Dog ('skin_nodules') must return 400
        bad_sym_resp = self.client.post(
            "/api/symptoms/submit",
            json={
                "animal": "dog",
                "symptoms": ["skin_nodules"],
            },
        )
        self.assertEqual(bad_sym_resp.status_code, 400)

    def test_06_combined_decision_agreement_and_conflict(self):
        img_lsd = {
            "predictedClass": "lumpy_skin_disease",
            "predictedLabel": "Lumpy Skin Disease (LSD)",
            "confidence": 84.0,
            "isLowConfidence": False,
            "preventionTips": ["Isolate affected cattle."],
        }
        sym_lsd = {
            "topConditionId": "lumpy_skin_disease",
            "topCondition": "Lumpy Skin Disease (LSD)",
            "matchScorePercent": 80.0,
            "preventionTips": ["Practice vector control."],
        }
        sym_fmd = {
            "topConditionId": "foot_and_mouth_disease",
            "topCondition": "Foot-and-Mouth Disease (FMD)",
            "matchScorePercent": 90.0,
            "preventionTips": ["Quarantine livestock."],
        }

        agree_decision = evaluate_combined_decision("cow", img_lsd, sym_lsd)
        self.assertFalse(agree_decision["hasConflict"])
        self.assertFalse(agree_decision["isUncertain"])

        conflict_decision = evaluate_combined_decision("cow", img_lsd, sym_fmd)
        self.assertTrue(conflict_decision["hasConflict"])
        self.assertTrue(conflict_decision["isUncertain"])

        # Test combined endpoint via HTTP
        comb_resp = self.client.post(
            "/api/predict/combined",
            json={
                "animal": "cow",
                "imagePredictionData": img_lsd,
                "symptoms": ["mouth_hoof_blisters", "excessive_salivation", "fever"],
            },
        )
        self.assertEqual(comb_resp.status_code, 200)
        comb_data = comb_resp.get_json()
        self.assertTrue(comb_data["combinedDecision"]["hasConflict"])

    def test_07_history_filtering_and_deletion(self):
        # Create a prediction record
        create_resp = self.client.post(
            "/api/predictions",
            json={
                "animal": "Buffalo",
                "imagePrediction": "Foot-and-Mouth Disease (FMD)",
                "confidence": 88.5,
                "symptoms": ["Fever (High body temperature)"],
                "symptomAnalysis": "High symptom match for FMD",
            },
        )
        self.assertEqual(create_resp.status_code, 201)
        rec_id = create_resp.get_json()["record"]["id"]

        # Filter history by animal=buffalo
        hist_resp = self.client.get("/api/history?animal=buffalo")
        self.assertEqual(hist_resp.status_code, 200)
        records = hist_resp.get_json()["records"]
        self.assertTrue(any(r["id"] == rec_id for r in records))

        # Delete the single record
        del_resp = self.client.delete(f"/api/history/{rec_id}")
        self.assertEqual(del_resp.status_code, 200)

        # Verify record is gone
        get_deleted = self.client.get(f"/api/history/{rec_id}")
        self.assertEqual(get_deleted.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
