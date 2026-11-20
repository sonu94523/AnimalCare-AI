"""
Isolated pytest test suite for AnimalCare AI.

Uses in-memory SQLite (`sqlite:///:memory:`) and `tmp_path` directories for
uploads, datasets, and model checkpoints so running tests never modifies
`backend/database/`, `backend/uploads/`, `ml/dataset/`, or `ml/saved_models/`.
"""

import io
import os
import re
import numpy as np
import pytest
import torch
from PIL import Image

from backend.app import create_app
from backend.domain_data import INITIAL_ANIMALS, INITIAL_DISEASES, SYMPTOM_CATALOG
from backend.services.decision_service import evaluate_combined_decision
from backend.services.prediction_service import clear_model_cache
from backend.services.symptom_service import analyze_symptoms, resolve_symptom_ids
from ml.constants import WEIGHTS_FILENAME
from ml.evaluate import compute_classification_metrics, compute_confusion_matrix, evaluate_saved_model
from ml.model import MobileNetV2DiseaseModel
from ml.preprocessing import CLASS_NAMES, IMAGE_SHAPE, preprocess_image, seed_sample_dataset
from ml.train import train_and_save_model


def _make_textured_jpeg(base_rgb=(165, 110, 80), size=(300, 240), with_exif=False) -> bytes:
    """Create a valid non-uniform JPEG image (high enough std to pass the blank-image check)."""
    rng = np.random.default_rng(7)
    arr = np.zeros((size[1], size[0], 3), dtype=np.float32)
    for c in range(3):
        arr[:, :, c] = np.clip(base_rgb[c] + rng.normal(0, 25, size=(size[1], size[0])), 0, 255)
    img = Image.fromarray(arr.astype(np.uint8), mode="RGB")
    buf = io.BytesIO()
    if with_exif:
        exif = img.getexif()
        exif[0x010E] = "Sensitive-GPS-Camera-Note"
        img.save(buf, format="JPEG", quality=90, exif=exif)
    else:
        img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _make_solid_jpeg(color=(0, 0, 0), size=(224, 224)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.fixture()
def isolated_env(tmp_path):
    """Build an isolated Flask app with no model weights initially."""
    clear_model_cache()
    upload_dir = tmp_path / "uploads"
    models_dir = tmp_path / "saved_models"
    dataset_dir = tmp_path / "dataset"
    upload_dir.mkdir()
    models_dir.mkdir()
    dataset_dir.mkdir()

    app = create_app(
        config={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "UPLOAD_FOLDER": str(upload_dir),
            "MODELS_DIR": str(models_dir),
            "DATASET_DIR": str(dataset_dir),
            "ADMIN_TOKEN": "test-secret-token",
            "CORS_ORIGINS": ["http://localhost:5173"],
        }
    )
    return {
        "app": app,
        "client": app.test_client(),
        "upload_dir": upload_dir,
        "models_dir": models_dir,
        "dataset_dir": dataset_dir,
        "admin_headers": {"X-Admin-Token": "test-secret-token"},
    }


@pytest.fixture(scope="module")
def trained_artifacts(tmp_path_factory):
    """Train a small fast checkpoint once per test run in a temp directory (offline, no ImageNet download)."""
    base = tmp_path_factory.mktemp("trained_model")
    dataset_dir = base / "dataset"
    models_dir = base / "saved_models"
    dataset_dir.mkdir()
    models_dir.mkdir()

    seed_sample_dataset(dataset_root=str(dataset_dir), raw_samples_per_class=6, seed=123)
    train_result = train_and_save_model(
        dataset_root=str(dataset_dir),
        saved_models_dir=str(models_dir),
        epochs=4,
        batch_size=6,
        learning_rate=3e-3,
        unfreeze_top=1,
        pretrained=False,
        augment=False,
        seed=123,
    )
    clear_model_cache()
    return {
        "dataset_dir": dataset_dir,
        "models_dir": models_dir,
        "train_result": train_result,
    }


@pytest.fixture()
def trained_env(tmp_path, trained_artifacts):
    """Isolated Flask app & fresh in-memory DB pointing at the module-scoped trained checkpoint."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    app = create_app(
        config={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "UPLOAD_FOLDER": str(upload_dir),
            "MODELS_DIR": str(trained_artifacts["models_dir"]),
            "DATASET_DIR": str(trained_artifacts["dataset_dir"]),
            "ADMIN_TOKEN": "test-secret-token",
            "CORS_ORIGINS": ["http://localhost:5173"],
        }
    )
    return {
        "app": app,
        "client": app.test_client(),
        "upload_dir": upload_dir,
        "models_dir": trained_artifacts["models_dir"],
        "dataset_dir": trained_artifacts["dataset_dir"],
        "admin_headers": {"X-Admin-Token": "test-secret-token"},
        "train_result": trained_artifacts["train_result"],
    }


def test_health_animals_diseases_and_model_info(isolated_env):
    client = isolated_env["client"]

    health = client.get("/api/health").get_json()
    assert health["status"] == "ok"
    assert sorted(health["aiSupportedAnimals"]) == ["buffalo", "cow"]
    assert health["modelLoaded"] is False
    assert health["modelValidated"] is False

    animals = client.get("/api/animals").get_json()["animals"]
    assert len(animals) == 6
    assert {a["id"] for a in animals if a["aiSupported"]} == {"cow", "buffalo"}
    assert {a["id"] for a in animals if not a["aiSupported"]} == {"goat", "sheep", "dog", "cat"}

    diseases = client.get("/api/diseases").get_json()["diseases"]
    assert len(diseases) >= 3
    assert {d["id"] for d in diseases} == {"lumpy_skin_disease", "foot_and_mouth_disease", "healthy"}

    info = client.get("/api/model/info").get_json()
    assert info["backbone"] == "MobileNetV2"
    assert info["inputShape"] == [224, 224, 3]
    assert info["validated"] is False
    assert info["modelLoaded"] is False
    assert "not been validated" in info["statusNote"].lower()


def test_fail_closed_503_when_weights_missing(isolated_env):
    """Server must return 503 and NEVER train inside an HTTP request when weights are missing."""
    client = isolated_env["client"]
    jpeg = _make_textured_jpeg()

    resp = client.post(
        "/api/predict/image",
        data={"animal": "cow", "image": (io.BytesIO(jpeg), "cow.jpg")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 503
    assert "not installed" in resp.get_json()["error"].lower()
    # Confirm no checkpoint was secretly created and the uploaded file was cleaned up
    assert list(isolated_env["models_dir"].iterdir()) == []
    assert list(isolated_env["upload_dir"].iterdir()) == []


def test_preprocessing_consistent_between_bytes_and_path(tmp_path):
    jpeg = _make_textured_jpeg()
    img_path = tmp_path / "sample.jpg"
    img_path.write_bytes(jpeg)

    from_bytes = preprocess_image(jpeg, normalization="imagenet", expand_dims=True)
    from_path = preprocess_image(str(img_path), normalization="imagenet", expand_dims=True)

    assert from_bytes.shape == (1, *IMAGE_SHAPE)
    assert np.allclose(from_bytes, from_path, atol=1e-5)


def test_training_lowers_loss_and_evaluate_metrics_math(trained_env):
    history = trained_env["train_result"]["report"]["history"]
    assert len(history) == 4
    assert history[-1]["trainLoss"] < history[0]["trainLoss"]
    assert trained_env["train_result"]["report"]["trainingData"] == "synthetic"
    assert trained_env["train_result"]["report"]["validated"] is False

    # Verify exact hand-computed metrics in evaluate.py
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 1, 1, 1, 2, 0])
    cm = compute_confusion_matrix(y_true, y_pred, num_classes=3)
    assert cm == [[1, 1, 0], [0, 2, 0], [1, 0, 1]]

    metrics = compute_classification_metrics(y_true, y_pred, CLASS_NAMES)
    assert metrics["totalSamples"] == 6
    assert metrics["accuracyPercent"] == pytest.approx(66.67, abs=0.01)
    assert metrics["perClass"]["healthy"]["precision"] == 50.0
    assert metrics["perClass"]["healthy"]["recall"] == 50.0
    assert metrics["perClass"]["lumpy_skin_disease"]["recall"] == 100.0
    assert metrics["perClass"]["foot_and_mouth_disease"]["precision"] == 100.0

    # End-to-end evaluate_saved_model on tmp_path
    eval_out = evaluate_saved_model(
        dataset_root=str(trained_env["dataset_dir"]),
        saved_models_dir=str(trained_env["models_dir"]),
        split_name="test",
    )
    assert eval_out["report"]["evaluationData"] == "synthetic"
    assert eval_out["report"]["validated"] is False


def test_solid_black_and_white_images_are_never_confident_disease(trained_env):
    """A solid-black or solid-white image must be flagged unsuitable/uncertain, not FMD/LSD."""
    client = trained_env["client"]
    for color, name in [((0, 0, 0), "black.jpg"), ((255, 255, 255), "white.jpg")]:
        resp = client.post(
            "/api/predict/image",
            data={"animal": "cow", "image": (io.BytesIO(_make_solid_jpeg(color)), name)},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        pred = resp.get_json()["prediction"]
        assert pred["isOutOfDistribution"] is True
        assert pred["isLowConfidence"] is True
        assert pred["confidence"] == 0.0
        assert pred["predictedClass"] == "uncertain"
        assert all("quarantine" not in tip.lower() for tip in pred["preventionTips"])


def test_upload_hardening_exif_stripped_nosniff_and_rejections(trained_env):
    client = trained_env["client"]

    # 1. Valid upload with EXIF metadata -> EXIF must be stripped on disk & nosniff header sent
    exif_jpeg = _make_textured_jpeg(with_exif=True)
    resp = client.post(
        "/api/predict/image",
        data={"animal": "cow", "image": (io.BytesIO(exif_jpeg), "cow_exif.jpg")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["uploadId"]
    assert body["prediction"]["modelValidated"] is False

    saved_filename = body["upload"]["filename"]
    saved_path = trained_env["upload_dir"] / saved_filename
    assert saved_path.is_file()
    with Image.open(saved_path) as saved_img:
        assert len(saved_img.getexif()) == 0

    served = client.get(f"/uploads/{saved_filename}")
    assert served.status_code == 200
    assert served.headers.get("X-Content-Type-Options") == "nosniff"
    served.close()

    # 2. Unsupported animal -> 400
    bad_animal = client.post(
        "/api/predict/image",
        data={"animal": "goat", "image": (io.BytesIO(exif_jpeg), "goat.jpg")},
        content_type="multipart/form-data",
    )
    assert bad_animal.status_code == 400

    # 3. Invalid extension -> 400
    bad_ext = client.post(
        "/api/predict/image",
        data={"animal": "cow", "image": (io.BytesIO(b"plain text"), "notes.txt")},
        content_type="multipart/form-data",
    )
    assert bad_ext.status_code == 400

    # 4. Corrupt bytes with .jpg extension -> 400
    corrupt = client.post(
        "/api/predict/image",
        data={"animal": "cow", "image": (io.BytesIO(b"\xff\xd8\xffcorrupt"), "bad.jpg")},
        content_type="multipart/form-data",
    )
    assert corrupt.status_code == 400

    # 5. Oversized payload (> 5 MB) -> 413
    oversized = client.post(
        "/api/predict/image",
        data={"animal": "cow", "image": (io.BytesIO(b"0" * (5 * 1024 * 1024 + 1024)), "huge.jpg")},
        content_type="multipart/form-data",
    )
    assert oversized.status_code == 413


def test_combined_rejects_client_forged_predictions_and_accepts_upload_id(trained_env):
    client = trained_env["client"]

    # Forged imagePredictionData must be rejected with 400
    forged = client.post(
        "/api/predict/combined",
        json={
            "animal": "cow",
            "imagePredictionData": {
                "predictedClass": "foot_and_mouth_disease",
                "confidence": 99.9,
                "imagePrediction": "FORGED",
            },
            "symptoms": ["fever"],
        },
    )
    assert forged.status_code == 400

    # Arbitrary external imagePath must be rejected with 400
    evil_path = client.post(
        "/api/predict/combined",
        json={
            "animal": "cow",
            "imagePath": "//evil.example/x.png",
            "symptoms": ["fever"],
        },
    )
    assert evil_path.status_code == 400

    # Legitimate server-side upload -> uploadId lookup succeeds
    up_resp = client.post(
        "/api/upload",
        data={"animal": "cow", "image": (io.BytesIO(_make_textured_jpeg()), "cow.jpg")},
        content_type="multipart/form-data",
    )
    assert up_resp.status_code == 201
    upload_id = up_resp.get_json()["uploadId"]

    comb_resp = client.post(
        "/api/predict/combined",
        json={
            "animal": "cow",
            "uploadId": upload_id,
            "symptoms": ["mouth_hoof_blisters", "excessive_salivation", "fever"],
        },
    )
    assert comb_resp.status_code == 200
    comb_body = comb_resp.get_json()
    assert comb_body["imageResult"] is not None
    assert comb_body["symptomResult"]["topConditionId"] == "foot_and_mouth_disease"
    assert comb_body["record"]["imagePath"].startswith("/uploads/")


def test_malformed_and_non_dict_json_returns_400(isolated_env):
    client = isolated_env["client"]

    for endpoint in ("/api/symptoms/submit", "/api/predict/combined"):
        bad_syntax = client.post(endpoint, data="{bad json", content_type="application/json")
        assert bad_syntax.status_code == 400

        non_dict = client.post(endpoint, json=["not", "a", "dict"])
        assert non_dict.status_code == 400


def test_symptom_rules_and_decision_logic(isolated_env):
    client = isolated_env["client"]

    # LSD match for Cow
    lsd = client.post(
        "/api/symptoms/submit",
        json={"animal": "cow", "symptoms": ["skin_nodules", "fever", "swelling", "reduced_milk"]},
    )
    assert lsd.status_code == 200
    assert lsd.get_json()["topConditionId"] == "lumpy_skin_disease"
    assert lsd.get_json()["matchScorePercent"] >= 60.0

    # FMD match for Buffalo
    fmd = client.post(
        "/api/symptoms/submit",
        json={"animal": "buffalo", "symptoms": ["mouth_hoof_blisters", "excessive_salivation", "difficulty_walking"]},
    )
    assert fmd.status_code == 200
    assert fmd.get_json()["topConditionId"] == "foot_and_mouth_disease"

    # Single non-specific symptom -> inconclusive
    dog_ids, _, err = resolve_symptom_ids("dog", ["fever"])
    assert err == ""
    assert analyze_symptoms("dog", dog_ids)["topConditionId"] == "inconclusive"

    # Inapplicable symptom for dog -> 400
    bad_sym = client.post("/api/symptoms/submit", json={"animal": "dog", "symptoms": ["skin_nodules"]})
    assert bad_sym.status_code == 400

    # Decision service agreement vs conflict
    img_lsd = {"predictedClass": "lumpy_skin_disease", "predictedLabel": "Lumpy Skin Disease (LSD)", "confidence": 84.0, "isLowConfidence": False, "modelValidated": False}
    sym_lsd = {"topConditionId": "lumpy_skin_disease", "topCondition": "Lumpy Skin Disease (LSD)", "matchScorePercent": 80.0}
    sym_fmd = {"topConditionId": "foot_and_mouth_disease", "topCondition": "Foot-and-Mouth Disease (FMD)", "matchScorePercent": 90.0}

    agree = evaluate_combined_decision("cow", img_lsd, sym_lsd)
    assert agree["hasConflict"] is False
    assert "Agreement" in agree["agreementStatus"]

    conflict = evaluate_combined_decision("cow", img_lsd, sym_fmd)
    assert conflict["hasConflict"] is True
    assert conflict["isUncertain"] is True


def test_history_admin_auth_and_file_cleanup_on_delete(trained_env):
    client = trained_env["client"]
    headers = trained_env["admin_headers"]

    # Create a prediction with an uploaded image
    pred_resp = client.post(
        "/api/predict/image",
        data={"animal": "buffalo", "image": (io.BytesIO(_make_textured_jpeg()), "buf.jpg")},
        content_type="multipart/form-data",
    )
    assert pred_resp.status_code == 200
    rec_id = pred_resp.get_json()["record"]["id"]
    img_file = trained_env["upload_dir"] / pred_resp.get_json()["upload"]["filename"]
    assert img_file.is_file()

    # Unauthenticated DELETE must fail with 401
    assert client.delete(f"/api/history/{rec_id}").status_code == 401
    assert client.delete("/api/history").status_code == 401

    # Wrong token must fail with 401
    assert client.delete(f"/api/history/{rec_id}", headers={"X-Admin-Token": "wrong"}).status_code == 401

    # Filter history by animal and verify full details payload is persisted for faithful History replay
    filtered = client.get("/api/history?animal=buffalo").get_json()["records"]
    matched = [r for r in filtered if r["id"] == rec_id]
    assert len(matched) == 1
    assert matched[0]["details"]["combinedDecision"] is not None
    assert matched[0]["details"]["imageResult"]["classProbabilities"]
    assert matched[0]["details"]["preventionTips"]

    # Authenticated DELETE removes both the DB row and the uploaded file
    del_resp = client.delete(f"/api/history/{rec_id}", headers=headers)
    assert del_resp.status_code == 200
    assert not img_file.exists()
    assert client.get(f"/api/history/{rec_id}").status_code == 404

    # Bulk clear removes remaining rows & files
    client.post("/api/symptoms/submit", json={"animal": "cow", "symptoms": ["fever"]})
    clear_resp = client.delete("/api/history", headers=headers)
    assert clear_resp.status_code == 200
    assert client.get("/api/history").get_json()["totalCount"] == 0


def test_clear_history_removes_orphaned_uploads_and_combined_validates_symptoms_first(trained_env):
    """Regression test for Issue 2: no orphaned files on disk after clear-all or invalid combined submit."""
    client = trained_env["client"]
    headers = trained_env["admin_headers"]
    upload_dir = trained_env["upload_dir"]

    # 1. Upload via /api/upload without completing a screening (only UploadRecord exists, no Prediction row)
    up_resp = client.post(
        "/api/upload",
        data={"animal": "cow", "image": (io.BytesIO(_make_textured_jpeg()), "unfinished.jpg")},
        content_type="multipart/form-data",
    )
    assert up_resp.status_code == 201
    orphan_file = upload_dir / up_resp.get_json()["upload"]["filename"]
    assert orphan_file.is_file()

    # Clear all history must also delete unfinished UploadRecord files
    clear_resp = client.delete("/api/history", headers=headers)
    assert clear_resp.status_code == 200
    assert not orphan_file.exists()
    assert list(upload_dir.iterdir()) == []

    # 2. Combined submit with a photo + invalid symptom list must reject BEFORE saving the file
    bad_comb = client.post(
        "/api/predict/combined",
        data={
            "animal": "cow",
            "symptoms": '["not_a_real_symptom"]',
            "image": (io.BytesIO(_make_textured_jpeg()), "cow.jpg"),
        },
        content_type="multipart/form-data",
    )
    assert bad_comb.status_code == 400
    assert list(upload_dir.iterdir()) == []


def test_per_epoch_on_the_fly_augmentation_preserves_originals():
    """Regression test for Issue 3: augmentation runs per batch inside fit() without mutating X_train."""
    batch = torch.rand((4, 3, 64, 64), dtype=torch.float32)
    snapshot = batch.clone()
    gen = torch.Generator().manual_seed(99)

    aug_epoch_1 = MobileNetV2DiseaseModel._augment_batch(batch, gen)
    aug_epoch_2 = MobileNetV2DiseaseModel._augment_batch(batch, gen)

    # Original tensor untouched, and consecutive epochs see different augmented variants
    assert torch.equal(batch, snapshot)
    assert not torch.allclose(aug_epoch_1, snapshot)
    assert not torch.allclose(aug_epoch_1, aug_epoch_2)


def test_strict_25m_pixel_cap_and_non_english_filename_and_iso_utc_timestamp(trained_env):
    """Regression tests for Issues 4, 5 and 6."""
    client = trained_env["client"]

    # Issue 4: 6000x5000 = 30M pixels (well under 5 MB as flat PNG, > 25M strict cap) must be rejected
    big_png_buf = io.BytesIO()
    Image.new("RGB", (6000, 5000), (120, 130, 140)).save(big_png_buf, format="PNG")
    big_png_bytes = big_png_buf.getvalue()
    assert len(big_png_bytes) < 5 * 1024 * 1024  # small byte size, huge pixel count

    over_px_resp = client.post(
        "/api/predict/image",
        data={"animal": "cow", "image": (io.BytesIO(big_png_bytes), "huge_dims.png")},
        content_type="multipart/form-data",
    )
    assert over_px_resp.status_code == 400
    assert "pixel" in over_px_resp.get_json()["error"].lower()

    # Issue 5: Non-English filename ('गाय.jpg') must be accepted and saved safely on disk
    hindi_resp = client.post(
        "/api/predict/image",
        data={"animal": "cow", "image": (io.BytesIO(_make_textured_jpeg()), "गाय.jpg")},
        content_type="multipart/form-data",
    )
    assert hindi_resp.status_code == 200
    hindi_body = hindi_resp.get_json()
    assert hindi_body["upload"]["originalName"] == "गाय.jpg"
    assert hindi_body["upload"]["filename"].endswith(".jpg")

    # Issue 6: History record exposes an explicit UTC ISO-8601 timestamp ending in 'Z'
    record = hindi_body["record"]
    assert record["createdAt"].endswith("Z")
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", record["createdAt"])


def test_unexpected_prediction_error_cleans_up_upload_and_health_checks_corrupt_weights(isolated_env, monkeypatch):
    """Regression tests for Smaller Items 3 and 4."""
    client = isolated_env["client"]

    # Smaller Item 4: Corrupt checkpoint file must report modelLoaded=False on /api/health
    corrupt_ckpt = isolated_env["models_dir"] / WEIGHTS_FILENAME
    corrupt_ckpt.write_bytes(b"not-a-valid-pytorch-checkpoint")
    clear_model_cache()
    health = client.get("/api/health").get_json()
    assert health["modelLoaded"] is False
    assert health["database"] == "sqlite"

    # Smaller Item 3: Unexpected inference exception must return 500 and delete the uploaded file
    def _boom(*_args, **_kwargs):
        raise RuntimeError("simulated inference crash")

    monkeypatch.setattr("backend.routes.api_routes.predict_disease_from_image", _boom)
    crash_resp = client.post(
        "/api/predict/image",
        data={"animal": "cow", "image": (io.BytesIO(_make_textured_jpeg()), "cow.jpg")},
        content_type="multipart/form-data",
    )
    assert crash_resp.status_code == 500
    assert list(isolated_env["upload_dir"].iterdir()) == []


def test_frontend_fallback_data_matches_backend_domain_data():
    """Regression test for Smaller Item 2: keep fallbackData.js IDs in sync with backend/domain_data.py."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fallback_path = os.path.join(repo_root, "frontend", "src", "data", "fallbackData.js")
    with open(fallback_path, "r", encoding="utf-8") as f:
        text = f.read()

    animals_block = text.split("export const OFFLINE_FALLBACK_ANIMALS")[1].split("export const OFFLINE_FALLBACK_SYMPTOMS")[0]
    symptoms_block = text.split("export const OFFLINE_FALLBACK_SYMPTOMS")[1].split("export const OFFLINE_FALLBACK_DISEASES")[0]
    diseases_block = text.split("export const OFFLINE_FALLBACK_DISEASES")[1]

    fe_animal_ids = re.findall(r"id:\s*'([^']+)'", animals_block)
    fe_symptom_ids = re.findall(r"id:\s*'([^']+)'", symptoms_block)
    fe_disease_ids = re.findall(r"id:\s*'([^']+)'", diseases_block)

    assert fe_animal_ids == [a["slug"] for a in INITIAL_ANIMALS]
    assert fe_symptom_ids == [s["id"] for s in SYMPTOM_CATALOG]
    assert fe_disease_ids == [d["slug"] for d in INITIAL_DISEASES]

    # Regression test for Issue 1: admin token must never be embedded via VITE_ADMIN_TOKEN
    for rel in ("frontend/src/services/api.js", "frontend/src/pages/History.jsx"):
        with open(os.path.join(repo_root, rel), "r", encoding="utf-8") as f:
            assert "VITE_ADMIN_TOKEN" not in f.read()

