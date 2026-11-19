"""
Rule-Based Symptom Analysis Engine for Preliminary Animal Disease Screening.

Evaluates user-selected clinical symptoms against weighted veterinary symptom
rules for supported animals (Cow, Buffalo, Goat, Sheep, Dog, Cat).
Provides transparent rule match scores, matched symptom breakdowns, honest
non-specific/inconclusive handling, and preventive care recommendations.
"""

from typing import Any, Dict, List, Set, Tuple

# Map both symptom IDs and human-readable labels to canonical symptom IDs
SYMPTOM_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "fever",
        "label": "Fever (High body temperature)",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "loss_of_appetite",
        "label": "Loss of appetite (Reduced feed intake)",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "coughing",
        "label": "Coughing or respiratory distress",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "diarrhea",
        "label": "Diarrhea",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "skin_lesions",
        "label": "Skin lesions / sores / scabs",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "swelling",
        "label": "Swelling (limbs, brisket, or lymph nodes)",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "weakness",
        "label": "Weakness / lethargy",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "difficulty_walking",
        "label": "Difficulty walking / lameness",
        "category": "general",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "reduced_milk",
        "label": "Reduced milk production",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep"],
    },
    {
        "id": "skin_nodules",
        "label": "Firm round skin nodules (2–5 cm) on head, neck, or body",
        "category": "specific",
        "animals": ["cow", "buffalo"],
    },
    {
        "id": "mouth_hoof_blisters",
        "label": "Blisters / vesicles on tongue, gums, muzzle, or hooves",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep"],
    },
    {
        "id": "excessive_salivation",
        "label": "Excessive ropy salivation / drooling",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "nasal_ocular_discharge",
        "label": "Nasal and ocular (watery eye) discharge",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep", "dog", "cat"],
    },
    {
        "id": "fur_hair_loss",
        "label": "Patchy hair/fur loss or frequent scratching",
        "category": "specific",
        "animals": ["dog", "cat"],
    },
]

ID_TO_LABEL: Dict[str, str] = {item["id"]: item["label"] for item in SYMPTOM_CATALOG}
LABEL_TO_ID: Dict[str, str] = {item["label"].lower(): item["id"] for item in SYMPTOM_CATALOG}

# Weighted disease rules:
# Hallmark symptoms carry higher weights (3.0 - 4.0); supporting symptoms carry 1.0 - 1.5.
DISEASE_RULES: List[Dict[str, Any]] = [
    {
        "conditionId": "lumpy_skin_disease",
        "name": "Lumpy Skin Disease (LSD)",
        "applicableAnimals": {"cow", "buffalo"},
        "hallmarkSymptoms": {"skin_nodules"},
        "weights": {
            "skin_nodules": 4.0,
            "skin_lesions": 2.0,
            "fever": 1.5,
            "swelling": 1.5,
            "reduced_milk": 1.0,
            "loss_of_appetite": 1.0,
            "nasal_ocular_discharge": 1.0,
            "weakness": 0.5,
        },
        "prevention": [
            "Immediately isolate the animal showing skin nodules or fever from the rest of the herd.",
            "Control blood-feeding insect vectors (mosquitoes, biting flies, ticks) in cattle sheds.",
            "Disinfect premises and contact a veterinarian for confirmatory LSD diagnosis and vaccination advice.",
        ],
    },
    {
        "conditionId": "foot_and_mouth_disease",
        "name": "Foot-and-Mouth Disease (FMD)",
        "applicableAnimals": {"cow", "buffalo", "goat", "sheep"},
        "hallmarkSymptoms": {"mouth_hoof_blisters", "excessive_salivation"},
        "weights": {
            "mouth_hoof_blisters": 4.0,
            "excessive_salivation": 2.5,
            "difficulty_walking": 2.0,
            "fever": 1.5,
            "reduced_milk": 1.0,
            "loss_of_appetite": 1.0,
            "weakness": 0.5,
        },
        "prevention": [
            "Strictly quarantine the affected animal and halt livestock movement to prevent FMD spread.",
            "Sanitize feeding troughs, water containers, footwear, and shed entrances.",
            "Provide soft, easily consumable feed and clean water while awaiting a veterinary officer.",
        ],
    },
    {
        "conditionId": "dermatological_skin_condition",
        "name": "Dermatological / Ectoparasitic Skin Irritation",
        "applicableAnimals": {"dog", "cat", "goat", "sheep"},
        "hallmarkSymptoms": {"fur_hair_loss", "skin_lesions"},
        "weights": {
            "fur_hair_loss": 3.5,
            "skin_lesions": 2.5,
            "swelling": 1.0,
            "loss_of_appetite": 0.5,
            "weakness": 0.5,
        },
        "prevention": [
            "Keep the animal's bedding clean and dry, and prevent scratching or biting at sores.",
            "Separate the animal from other pets or livestock in case of contagious mites or fungal infection.",
            "Consult a veterinarian for skin scraping or dermatological examination.",
        ],
    },
    {
        "conditionId": "respiratory_enteric_infection",
        "name": "General Respiratory / Gastrointestinal Distress",
        "applicableAnimals": {"cow", "buffalo", "goat", "sheep", "dog", "cat"},
        "hallmarkSymptoms": {"coughing", "diarrhea"},
        "weights": {
            "coughing": 2.5,
            "diarrhea": 2.5,
            "nasal_ocular_discharge": 2.0,
            "fever": 1.5,
            "loss_of_appetite": 1.0,
            "weakness": 1.0,
        },
        "prevention": [
            "Ensure constant access to clean drinking water to prevent dehydration.",
            "Keep the animal in a warm, draft-free, well-ventilated shelter away from healthy animals.",
            "Seek veterinary evaluation if fever, coughing, or diarrhea persists.",
        ],
    },
]


def resolve_symptom_ids(
    animal_id: str,
    raw_symptoms: List[str],
) -> Tuple[List[str], List[str], str]:
    """
    Validate and resolve user-submitted symptom IDs or labels for `animal_id`.
    Returns `(symptom_ids, symptom_labels, error_message)`.
    """
    allowed_for_animal = {
        s["id"]: s["label"]
        for s in SYMPTOM_CATALOG
        if animal_id in s["animals"]
    }

    resolved_ids: List[str] = []
    resolved_labels: List[str] = []
    seen: Set[str] = set()

    for raw in raw_symptoms:
        item = str(raw).strip()
        if not item:
            continue
        canonical_id = None
        if item in allowed_for_animal:
            canonical_id = item
        elif item.lower() in LABEL_TO_ID:
            candidate_id = LABEL_TO_ID[item.lower()]
            if candidate_id in allowed_for_animal:
                canonical_id = candidate_id

        if canonical_id is None:
            return [], [], f"Symptom '{item}' is not applicable to {animal_id.capitalize()}."

        if canonical_id not in seen:
            seen.add(canonical_id)
            resolved_ids.append(canonical_id)
            resolved_labels.append(allowed_for_animal[canonical_id])

    if not resolved_ids:
        return [], [], "Please select at least one valid symptom."

    return resolved_ids, resolved_labels, ""


def analyze_symptoms(
    animal_id: str,
    symptom_ids: List[str],
) -> Dict[str, Any]:
    """
    Evaluate `symptom_ids` against `DISEASE_RULES` for `animal_id` and return
    ranked condition matches, match score percentage, match confidence level,
    explanation summary, and preventive care recommendations.
    """
    normalized_animal = (animal_id or "cow").strip().lower()
    selected_set = set(symptom_ids)
    selected_labels = [ID_TO_LABEL.get(sid, sid) for sid in symptom_ids]

    ranked_matches: List[Dict[str, Any]] = []

    for rule in DISEASE_RULES:
        if normalized_animal not in rule["applicableAnimals"]:
            continue

        weights: Dict[str, float] = rule["weights"]
        max_possible_score = sum(weights.values())
        matched_ids = [sid for sid in symptom_ids if sid in weights]
        if not matched_ids:
            continue

        raw_score = sum(weights[sid] for sid in matched_ids)
        has_hallmark = bool(selected_set & rule["hallmarkSymptoms"])

        # Normalize score to 0..100%; cap non-hallmark general matches so fever alone never claims 80% LSD
        score_percent = (raw_score / max_possible_score) * 100.0
        if has_hallmark:
            score_percent = min(98.0, score_percent * 1.25)
        else:
            score_percent = min(48.0, score_percent)

        score_percent = round(score_percent, 1)
        matched_labels = [ID_TO_LABEL.get(sid, sid) for sid in matched_ids]

        ranked_matches.append(
            {
                "conditionId": rule["conditionId"],
                "conditionName": rule["name"],
                "matchScorePercent": score_percent,
                "hasHallmarkSymptom": has_hallmark,
                "matchedSymptomCount": len(matched_ids),
                "matchedSymptoms": matched_labels,
                "preventionTips": rule["prevention"],
            }
        )

    ranked_matches.sort(
        key=lambda m: (m["hasHallmarkSymptom"], m["matchScorePercent"], m["matchedSymptomCount"]),
        reverse=True,
    )

    animal_name = normalized_animal.capitalize()

    if not ranked_matches or ranked_matches[0]["matchScorePercent"] < 25.0:
        top_condition = "Non-Specific Clinical Signs (Veterinary Exam Required)"
        top_condition_id = "inconclusive"
        top_score = ranked_matches[0]["matchScorePercent"] if ranked_matches else 0.0
        match_level = "Low / Non-Specific Match"
        summary = (
            f"Observed {len(selected_labels)} general symptom(s) for {animal_name}. "
            "No specific hallmark signs (such as skin nodules or mouth/hoof blisters) were reported, "
            "so the condition remains inconclusive. Please consult a veterinarian."
        )
        prevention_tips = [
            "Isolate the animal from the healthy herd or other pets as a precaution.",
            "Provide clean water, shade/dry shelter, and monitor body temperature.",
            "Consult a qualified veterinarian for physical examination.",
        ]
    else:
        best = ranked_matches[0]
        top_condition = best["conditionName"]
        top_condition_id = best["conditionId"]
        top_score = best["matchScorePercent"]
        prevention_tips = best["preventionTips"]

        if top_score >= 60.0 and best["hasHallmarkSymptom"]:
            match_level = "High Symptom Match"
            summary = (
                f"High rule-based symptom match ({top_score}%) for {top_condition} in {animal_name} "
                f"based on {best['matchedSymptomCount']} matching sign(s), including characteristic hallmark indicators."
            )
        else:
            match_level = "Moderate / Possible Match"
            summary = (
                f"Possible symptom overlap ({top_score}%) with {top_condition} in {animal_name} "
                f"({best['matchedSymptomCount']} matching sign(s)). Because several symptoms are shared across livestock "
                "illnesses, veterinary confirmation is required."
            )

    return {
        "animalId": normalized_animal,
        "animal": animal_name,
        "selectedSymptomIds": symptom_ids,
        "selectedSymptoms": selected_labels,
        "symptomCount": len(selected_labels),
        "topConditionId": top_condition_id,
        "topCondition": top_condition,
        "matchScorePercent": top_score,
        "matchLevel": match_level,
        "matchedConditions": ranked_matches[:3],
        "symptomAnalysis": summary,
        "preventionTips": prevention_tips,
    }
