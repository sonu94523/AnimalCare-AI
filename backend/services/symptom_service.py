"""
Rule-Based Symptom Analysis Engine for Preliminary Animal Disease Screening.

Evaluates user-selected clinical symptoms against weighted veterinary rules
across all 10 supported animals (Cow, Buffalo, Goat, Sheep, Horse, Pig,
Chicken, Dog, Cat, Rabbit) and highlights urgent red-flag clinical signs.
"""

from typing import Any, Dict, List, Set, Tuple

from backend.domain_data import CONDITION_PREVENTION, RED_FLAG_SYMPTOMS, SYMPTOM_CATALOG

ID_TO_LABEL: Dict[str, str] = {item["id"]: item["label"] for item in SYMPTOM_CATALOG}
LABEL_TO_ID: Dict[str, str] = {item["label"].lower(): item["id"] for item in SYMPTOM_CATALOG}

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
        "prevention": CONDITION_PREVENTION["lumpy_skin_disease"],
    },
    {
        "conditionId": "foot_and_mouth_disease",
        "name": "Foot-and-Mouth Disease (FMD)",
        "applicableAnimals": {"cow", "buffalo", "goat", "sheep", "pig"},
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
        "prevention": CONDITION_PREVENTION["foot_and_mouth_disease"],
    },
    {
        "conditionId": "bovine_mastitis",
        "name": "Mastitis (Udder Infection)",
        "applicableAnimals": {"cow", "buffalo", "goat", "sheep"},
        "hallmarkSymptoms": {"swollen_hot_udder"},
        "weights": {
            "swollen_hot_udder": 4.5,
            "reduced_milk": 2.5,
            "fever": 1.5,
            "loss_of_appetite": 1.0,
            "weakness": 0.5,
        },
        "prevention": CONDITION_PREVENTION["bovine_mastitis"],
    },
    {
        "conditionId": "ppr_small_ruminants",
        "name": "Peste des Petits Ruminants (PPR)",
        "applicableAnimals": {"goat", "sheep"},
        "hallmarkSymptoms": {"mouth_ulcers_ppr"},
        "weights": {
            "mouth_ulcers_ppr": 4.0,
            "nasal_ocular_discharge": 2.0,
            "diarrhea": 2.0,
            "fever": 1.5,
            "coughing": 1.5,
            "loss_of_appetite": 1.0,
        },
        "prevention": CONDITION_PREVENTION["ppr_small_ruminants"],
    },
    {
        "conditionId": "equine_colic_laminitis",
        "name": "Equine Colic / Laminitis Indicators",
        "applicableAnimals": {"horse"},
        "hallmarkSymptoms": {"abdominal_pain_rolling", "difficulty_walking"},
        "weights": {
            "abdominal_pain_rolling": 4.5,
            "difficulty_walking": 3.0,
            "loss_of_appetite": 1.5,
            "weakness": 1.0,
            "unable_to_stand": 2.0,
        },
        "prevention": CONDITION_PREVENTION["equine_colic_laminitis"],
    },
    {
        "conditionId": "swine_fever_signs",
        "name": "Swine Fever Warning Signs",
        "applicableAnimals": {"pig"},
        "hallmarkSymptoms": {"skin_red_purple_patches", "bloody_diarrhea"},
        "weights": {
            "skin_red_purple_patches": 4.0,
            "bloody_diarrhea": 3.0,
            "fever": 1.5,
            "vomiting": 1.5,
            "weakness": 1.0,
            "difficulty_walking": 1.0,
        },
        "prevention": CONDITION_PREVENTION["swine_fever_signs"],
    },
    {
        "conditionId": "newcastle_poultry_disease",
        "name": "Newcastle Disease (Ranikhet) Indicators",
        "applicableAnimals": {"chicken"},
        "hallmarkSymptoms": {"twisted_neck_paralysis", "ruffled_feathers_drooping"},
        "weights": {
            "twisted_neck_paralysis": 4.5,
            "ruffled_feathers_drooping": 3.0,
            "coughing": 1.5,
            "diarrhea": 1.5,
            "nasal_ocular_discharge": 1.0,
            "loss_of_appetite": 1.0,
        },
        "prevention": CONDITION_PREVENTION["newcastle_poultry_disease"],
    },
    {
        "conditionId": "canine_parvovirus_signs",
        "name": "Canine Parvovirus / Acute Gastroenteritis Signs",
        "applicableAnimals": {"dog"},
        "hallmarkSymptoms": {"bloody_diarrhea", "vomiting"},
        "weights": {
            "bloody_diarrhea": 4.0,
            "vomiting": 3.0,
            "diarrhea": 2.0,
            "fever": 1.5,
            "loss_of_appetite": 1.0,
            "weakness": 1.0,
        },
        "prevention": CONDITION_PREVENTION["canine_parvovirus_signs"],
    },
    {
        "conditionId": "feline_upper_respiratory",
        "name": "Feline Upper Respiratory Infection (URI)",
        "applicableAnimals": {"cat"},
        "hallmarkSymptoms": {"nasal_ocular_discharge", "coughing"},
        "weights": {
            "nasal_ocular_discharge": 3.5,
            "coughing": 3.0,
            "fever": 1.5,
            "loss_of_appetite": 1.5,
            "weakness": 1.0,
        },
        "prevention": CONDITION_PREVENTION["feline_upper_respiratory"],
    },
    {
        "conditionId": "rabbit_ear_mites_gi_stasis",
        "name": "Rabbit GI Stasis / Ear Mite Indicators",
        "applicableAnimals": {"rabbit"},
        "hallmarkSymptoms": {"stopped_droppings", "head_tilt_ear_crusts"},
        "weights": {
            "stopped_droppings": 4.5,
            "head_tilt_ear_crusts": 4.0,
            "loss_of_appetite": 2.0,
            "weakness": 1.0,
            "fur_hair_loss": 1.0,
        },
        "prevention": CONDITION_PREVENTION["rabbit_ear_mites_gi_stasis"],
    },
    {
        "conditionId": "dermatological_skin_condition",
        "name": "Dermatological / Ectoparasitic Skin Irritation",
        "applicableAnimals": {"dog", "cat", "goat", "sheep", "horse", "pig", "rabbit"},
        "hallmarkSymptoms": {"fur_hair_loss", "skin_lesions", "head_tilt_ear_crusts"},
        "weights": {
            "fur_hair_loss": 3.5,
            "skin_lesions": 2.5,
            "head_tilt_ear_crusts": 2.0,
            "swelling": 1.0,
            "loss_of_appetite": 0.5,
            "weakness": 0.5,
        },
        "prevention": CONDITION_PREVENTION["dermatological_skin_condition"],
    },
    {
        "conditionId": "respiratory_enteric_infection",
        "name": "General Respiratory / Gastrointestinal Distress",
        "applicableAnimals": {"cow", "buffalo", "goat", "sheep", "horse", "pig", "chicken", "dog", "cat", "rabbit"},
        "hallmarkSymptoms": {"coughing", "diarrhea"},
        "weights": {
            "coughing": 2.5,
            "diarrhea": 2.5,
            "nasal_ocular_discharge": 2.0,
            "fever": 1.5,
            "loss_of_appetite": 1.0,
            "weakness": 1.0,
        },
        "prevention": CONDITION_PREVENTION["respiratory_enteric_infection"],
    },
]


def resolve_symptom_ids(
    animal_id: str,
    raw_symptoms: List[str],
) -> Tuple[List[str], List[str], str]:
    """Validate and resolve symptom IDs (or legacy display labels) for `animal_id`."""
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
    """Evaluate `symptom_ids` against `DISEASE_RULES` for `animal_id`."""
    normalized_animal = (animal_id or "cow").strip().lower()
    selected_set = set(symptom_ids)
    selected_labels = [ID_TO_LABEL.get(sid, sid) for sid in symptom_ids]
    red_flags_present = [ID_TO_LABEL.get(sid, sid) for sid in symptom_ids if sid in RED_FLAG_SYMPTOMS]

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
            "No specific hallmark signs were reported, so the condition remains inconclusive. "
            "Please consult a veterinarian."
        )
        prevention_tips = CONDITION_PREVENTION["inconclusive"]
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
                f"({best['matchedSymptomCount']} matching sign(s)). Veterinary confirmation is required."
            )

    urgency_notice = None
    if red_flags_present:
        urgency_notice = (
            f"Urgent clinical red flag reported ({', '.join(red_flags_present)}). "
            "Contact a veterinarian immediately without waiting."
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
        "hasRedFlag": bool(red_flags_present),
        "redFlags": red_flags_present,
        "urgencyNotice": urgency_notice,
        "matchedConditions": ranked_matches[:3],
        "symptomAnalysis": summary,
        "preventionTips": prevention_tips,
    }
