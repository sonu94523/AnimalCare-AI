"""
Combined Image + Symptom Decision Engine & Uncertainty/Conflict Handler.

Synthesizes MobileNetV2 image classification output and rule-based clinical
symptom analysis into a transparent preliminary assessment:
  - Handles out-of-distribution / unsuitable images honestly
  - Highlights agreement when visual and symptomatic evidence align
  - Explicitly flags conflict/disagreement when image and symptom findings differ
  - Flags uncertainty when image confidence (< 60%) or symptom match is low
  - Carries forward `modelValidated` / `trainingData` so the UI never presents
    unvalidated synthetic-demo outputs as confirmed diagnostics.
"""

from typing import Any, Dict, List, Optional


def evaluate_combined_decision(
    animal_id: str,
    image_result: Optional[Dict[str, Any]] = None,
    symptom_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    animal_name = (animal_id or "cow").strip().capitalize()

    # Mode 1: Both Image and Symptoms provided
    if image_result and symptom_result:
        img_ood = bool(image_result.get("isOutOfDistribution"))
        has_img_classifier = bool(image_result.get("hasDiseaseClassifier", True))
        img_class = image_result.get("predictedClass")
        img_label = image_result.get("predictedLabel", "Unknown")
        img_conf = float(image_result.get("confidence") or 0.0)
        img_low_conf = bool(image_result.get("isLowConfidence", img_conf < 60.0))
        model_validated = bool(image_result.get("modelValidated", False))
        training_data = image_result.get("trainingData", "unknown")

        sym_cond_id = symptom_result.get("topConditionId")
        sym_cond_name = symptom_result.get("topCondition", "Non-Specific Clinical Signs")
        sym_score = float(symptom_result.get("matchScorePercent") or 0.0)

        merged_tips: List[str] = []
        for tip in (symptom_result.get("preventionTips") or []) + (image_result.get("preventionTips") or []):
            if tip not in merged_tips:
                merged_tips.append(tip)

        if not has_img_classifier and not img_ood:
            is_low = sym_score < 60.0 or sym_cond_id == "inconclusive"
            return {
                "mode": "combined",
                "animal": animal_name,
                "finalConclusion": f"Symptom-Guided Indication: {sym_cond_name}",
                "agreementStatus": "Photo Attached + Species Symptom Analysis",
                "combinedConfidence": round(sym_score, 1),
                "isUncertain": is_low,
                "hasConflict": False,
                "modelValidated": False,
                "trainingData": "symptom_rules",
                "explanation": (
                    f"Uploaded {animal_name} photo is verified and attached for veterinary reference. "
                    f"Clinical symptom analysis indicates '{sym_cond_name}' ({sym_score}% rule match)."
                ),
                "preventionTips": symptom_result.get("preventionTips") or [],
            }

        if img_ood:
            return {
                "mode": "combined",
                "animal": animal_name,
                "finalConclusion": f"Symptom Indication Only: {sym_cond_name} (Image Unsuitable)",
                "agreementStatus": "Image Unsuitable — Relying on Symptoms Only",
                "combinedConfidence": round(sym_score, 1),
                "isUncertain": True,
                "hasConflict": False,
                "modelValidated": model_validated,
                "trainingData": training_data,
                "explanation": (
                    f"The uploaded image could not be classified ({image_result.get('uncertaintyNotice')}). "
                    f"Symptom analysis reported '{sym_cond_name}' ({sym_score}% match)."
                ),
                "preventionTips": symptom_result.get("preventionTips") or [],
            }

        if img_class == sym_cond_id and not img_low_conf and sym_score >= 45.0:
            combined_score = round(0.55 * img_conf + 0.45 * sym_score, 1)
            return {
                "mode": "combined",
                "animal": animal_name,
                "finalConclusion": f"Consistent Indication: {img_label}",
                "agreementStatus": "Agreement (Image & Symptoms Consistent)",
                "combinedConfidence": combined_score,
                "isUncertain": not model_validated,
                "hasConflict": False,
                "modelValidated": model_validated,
                "trainingData": training_data,
                "explanation": (
                    f"Image output ({img_label} at {img_conf}%) and symptom rules "
                    f"({sym_cond_name} at {sym_score}%) both point to {img_label}. "
                    + (
                        "Note: the image model is not validated on real animals; rely on the clinical symptoms and consult a veterinarian."
                        if not model_validated
                        else "Consult a veterinarian for confirmation."
                    )
                ),
                "preventionTips": merged_tips,
            }

        if (
            sym_cond_id not in ("inconclusive", None)
            and img_class != sym_cond_id
            and sym_score >= 45.0
        ):
            combined_score = round(min(img_conf, sym_score), 1)
            return {
                "mode": "combined",
                "animal": animal_name,
                "finalConclusion": f"Conflicting Findings ({img_label} vs. {sym_cond_name})",
                "agreementStatus": "Conflict / Disagreement Detected",
                "combinedConfidence": combined_score,
                "isUncertain": True,
                "hasConflict": True,
                "modelValidated": model_validated,
                "trainingData": training_data,
                "explanation": (
                    f"Disagreement detected: image output indicates '{img_label}' ({img_conf}%), "
                    f"whereas reported symptoms match '{sym_cond_name}' ({sym_score}%). "
                    "Treat this screening as inconclusive and consult a veterinarian."
                ),
                "preventionTips": merged_tips,
            }

        combined_score = round(0.5 * img_conf + 0.5 * sym_score, 1)
        return {
            "mode": "combined",
            "animal": animal_name,
            "finalConclusion": f"Uncertain / Preliminary Indication ({img_label} / {sym_cond_name})",
            "agreementStatus": "Partial / Low-Confidence Evidence",
            "combinedConfidence": combined_score,
            "isUncertain": True,
            "hasConflict": False,
            "modelValidated": model_validated,
            "trainingData": training_data,
            "explanation": (
                f"Image output reported '{img_label}' ({img_conf}%) and symptoms reported "
                f"'{sym_cond_name}' ({sym_score}%). Evidence is partial or low-confidence; seek veterinary advice."
            ),
            "preventionTips": merged_tips,
        }

    # Mode 2: Image-Only Screening
    if image_result:
        img_ood = bool(image_result.get("isOutOfDistribution"))
        has_img_classifier = bool(image_result.get("hasDiseaseClassifier", True))
        img_label = image_result.get("predictedLabel", "Unknown")
        img_conf = float(image_result.get("confidence") or 0.0)
        img_low_conf = bool(image_result.get("isLowConfidence", img_conf < 60.0))
        model_validated = bool(image_result.get("modelValidated", False))
        training_data = image_result.get("trainingData", "unknown")

        if img_ood:
            return {
                "mode": "image_only",
                "animal": animal_name,
                "finalConclusion": "Uncertain / Unsuitable Image",
                "agreementStatus": "Out-of-Distribution / Blank Image Rejected",
                "combinedConfidence": 0.0,
                "isUncertain": True,
                "hasConflict": False,
                "modelValidated": model_validated,
                "trainingData": training_data,
                "explanation": image_result.get("uncertaintyNotice") or "Image could not be classified.",
                "preventionTips": image_result.get("preventionTips") or [],
            }

        if not has_img_classifier:
            return {
                "mode": "image_only",
                "animal": animal_name,
                "finalConclusion": f"Photo Verified for {animal_name} — Add Symptoms for Disease Screening",
                "agreementStatus": "Photo Attached (Species Symptom Check Needed)",
                "combinedConfidence": None,
                "isUncertain": True,
                "hasConflict": False,
                "modelValidated": False,
                "trainingData": "none",
                "explanation": image_result.get("summary") or f"Photo attached for {animal_name}.",
                "preventionTips": image_result.get("preventionTips") or [],
            }

        return {
            "mode": "image_only",
            "animal": animal_name,
            "finalConclusion": (
                f"Uncertain Image Output ({img_label})"
                if img_low_conf
                else f"Demo Image Output: {img_label}"
            ),
            "agreementStatus": (
                "Low Image Confidence (Symptom Check Recommended)"
                if img_low_conf
                else ("Demo Model Output — Not Clinically Validated" if not model_validated else "Image-Only Screening")
            ),
            "combinedConfidence": round(img_conf, 1),
            "isUncertain": img_low_conf or (not model_validated),
            "hasConflict": False,
            "modelValidated": model_validated,
            "trainingData": training_data,
            "explanation": (
                image_result.get("uncertaintyNotice")
                or f"MobileNetV2 demo output leaned toward {img_label} ({img_conf}%). "
                "Because this image model is not validated on real animals, always cross-check with symptoms and a veterinarian."
            ),
            "preventionTips": image_result.get("preventionTips") or [],
        }

    # Mode 3: Symptom-Only Screening
    if symptom_result:
        sym_cond_name = symptom_result.get("topCondition", "Non-Specific Clinical Signs")
        sym_score = float(symptom_result.get("matchScorePercent") or 0.0)
        is_low = sym_score < 60.0 or symptom_result.get("topConditionId") == "inconclusive"
        return {
            "mode": "symptom_only",
            "animal": animal_name,
            "finalConclusion": f"Symptom-Based Indication: {sym_cond_name}",
            "agreementStatus": (
                "Low / Non-Specific Symptom Evidence"
                if is_low
                else "Symptom-Only Screening (No Image Uploaded)"
            ),
            "combinedConfidence": round(sym_score, 1),
            "isUncertain": is_low,
            "hasConflict": False,
            "explanation": symptom_result.get("symptomAnalysis") or "",
            "preventionTips": symptom_result.get("preventionTips") or [],
        }

    return {
        "mode": "none",
        "animal": animal_name,
        "finalConclusion": "No Input Provided",
        "agreementStatus": "No Screening Data",
        "combinedConfidence": 0.0,
        "isUncertain": True,
        "hasConflict": False,
        "explanation": "Please upload an animal image or select observed symptoms to run screening.",
        "preventionTips": [],
    }
