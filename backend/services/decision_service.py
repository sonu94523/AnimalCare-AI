"""
Combined Image + Symptom Decision Engine & Uncertainty/Conflict Handler.

Synthesizes MobileNetV2 image classification output and rule-based clinical
symptom analysis into a transparent preliminary assessment:
  - Highlights agreement when visual and symptomatic evidence align
  - Explicitly flags conflict/disagreement when image and symptom findings differ
  - Flags uncertainty when image confidence (< 60%) or symptom match is low
"""

from typing import Any, Dict, List, Optional


def evaluate_combined_decision(
    animal_id: str,
    image_result: Optional[Dict[str, Any]] = None,
    symptom_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Combine `image_result` (from MobileNetV2) and `symptom_result` (from rule engine)
    into a unified screening decision with agreement and uncertainty metadata.
    """
    animal_name = (animal_id or "cow").strip().capitalize()

    # Mode 1: Both Image and Symptoms provided
    if image_result and symptom_result:
        img_class = image_result.get("predictedClass")
        img_label = image_result.get("predictedLabel", "Unknown")
        img_conf = float(image_result.get("confidence") or 0.0)
        img_low_conf = bool(image_result.get("isLowConfidence", img_conf < 60.0))

        sym_cond_id = symptom_result.get("topConditionId")
        sym_cond_name = symptom_result.get("topCondition", "Non-Specific Clinical Signs")
        sym_score = float(symptom_result.get("matchScorePercent") or 0.0)

        # Merge prevention tips without duplicates
        merged_tips: List[str] = []
        for tip in (image_result.get("preventionTips") or []) + (symptom_result.get("preventionTips") or []):
            if tip not in merged_tips:
                merged_tips.append(tip)

        # Case A: Image and Symptoms agree on LSD or FMD
        if img_class == sym_cond_id and not img_low_conf and sym_score >= 45.0:
            combined_score = round(0.55 * img_conf + 0.45 * sym_score, 1)
            return {
                "mode": "combined",
                "animal": animal_name,
                "finalConclusion": f"Consistent Indication: {img_label}",
                "agreementStatus": "Agreement (Image & Symptoms Consistent)",
                "combinedConfidence": combined_score,
                "isUncertain": False,
                "hasConflict": False,
                "explanation": (
                    f"Both MobileNetV2 image analysis ({img_label} at {img_conf}%) and clinical symptom rules "
                    f"({sym_cond_name} at {sym_score}%) independently support {img_label}. "
                    "Immediate isolation and veterinary confirmation are recommended."
                ),
                "preventionTips": merged_tips,
            }

        # Case B: Direct disagreement / conflict between image and symptoms
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
                "explanation": (
                    f"Disagreement detected: MobileNetV2 image screening indicates '{img_label}' ({img_conf}%), "
                    f"whereas reported symptoms match '{sym_cond_name}' ({sym_score}%). "
                    "Because visual appearance and clinical symptoms conflict, this screening is inconclusive. "
                    "Do not rely on automated output alone—consult a veterinarian for physical examination."
                ),
                "preventionTips": merged_tips,
            }

        # Case C: Low image confidence or non-specific symptoms
        combined_score = round(0.5 * img_conf + 0.5 * sym_score, 1)
        return {
            "mode": "combined",
            "animal": animal_name,
            "finalConclusion": f"Uncertain / Preliminary Indication ({img_label} / {sym_cond_name})",
            "agreementStatus": "Partial / Low-Confidence Evidence",
            "combinedConfidence": combined_score,
            "isUncertain": True,
            "hasConflict": False,
            "explanation": (
                f"Image screening reported '{img_label}' ({img_conf}% confidence) and symptom checking reported "
                f"'{sym_cond_name}' ({sym_score}% match). Because at least one source has low or non-specific confidence, "
                "treat this result as uncertain and seek veterinary advice."
            ),
            "preventionTips": merged_tips,
        }

    # Mode 2: Image-Only Screening
    if image_result:
        img_label = image_result.get("predictedLabel", "Unknown")
        img_conf = float(image_result.get("confidence") or 0.0)
        img_low_conf = bool(image_result.get("isLowConfidence", img_conf < 60.0))
        return {
            "mode": "image_only",
            "animal": animal_name,
            "finalConclusion": (
                f"Uncertain Image Screening ({img_label})"
                if img_low_conf
                else f"Image-Based Indication: {img_label}"
            ),
            "agreementStatus": (
                "Low Image Confidence (Symptom Check Recommended)"
                if img_low_conf
                else "Image-Only Screening (No Symptoms Provided)"
            ),
            "combinedConfidence": round(img_conf, 1),
            "isUncertain": img_low_conf,
            "hasConflict": False,
            "explanation": (
                image_result.get("uncertaintyNotice")
                or f"Based on visual features alone, MobileNetV2 classified the photo as {img_label} ({img_conf}% confidence). "
                "Adding clinical symptoms can help cross-check this visual screening."
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
