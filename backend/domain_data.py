"""
Single source of truth for AnimalCare AI domain data across 10 animal categories:
  - Livestock : Cow, Buffalo, Goat, Sheep, Horse, Pig
  - Poultry   : Chicken
  - Pets      : Dog, Cat, Rabbit

Note on AI coverage:
  - Cow & Buffalo have the MobileNetV2 3-class demo image classifier (not clinically validated)
    plus full weighted symptom rules.
  - All 10 animals support photo upload & visual quality verification, species-specific
    symptom screening, combined photo + symptom reports, and saved history.
"""

from typing import Any, Dict, List

AI_SUPPORTED_ANIMALS = {"cow", "buffalo"}
ALL_ANIMALS = {
    "cow",
    "buffalo",
    "goat",
    "sheep",
    "horse",
    "pig",
    "chicken",
    "dog",
    "cat",
    "rabbit",
}

RED_FLAG_SYMPTOMS = {"unable_to_stand", "bloody_diarrhea", "twisted_neck_paralysis"}

CONDITION_PREVENTION: Dict[str, List[str]] = {
    "lumpy_skin_disease": [
        "Isolate affected cattle immediately from the rest of the herd.",
        "Report suspected cases promptly to local veterinary authorities (LSD is a notifiable livestock disease).",
        "Control blood-feeding insect vectors (mosquitoes, biting flies, ticks) in sheds and follow regional vaccination schedules.",
        "Disinfect premises and avoid sharing needles or equipment between animals.",
    ],
    "foot_and_mouth_disease": [
        "Report suspected cases immediately to local veterinary authorities (FMD is a WOAH-listed notifiable disease).",
        "Strictly quarantine affected animals and halt livestock movement to prevent spread.",
        "Sanitize footbaths, sheds, footwear, and feeding troughs regularly.",
        "Provide soft, easily consumable feed and clean water while awaiting a veterinary officer.",
    ],
    "bovine_mastitis": [
        "Keep udder and milking area clean and dry; sanitize teats before and after milking.",
        "Milk affected animals last and discard abnormal milk safely—do not feed to calves.",
        "Consult a veterinarian promptly for culture-guided mastitis management.",
    ],
    "ppr_small_ruminants": [
        "Immediately isolate affected goats or sheep from the flock and restrict movement.",
        "Report suspected Peste des Petits Ruminants (PPR) to local veterinary authorities (notifiable disease).",
        "Provide clean drinking water, shade, and soft fodder while arranging veterinary care and flock vaccination.",
    ],
    "equine_colic_laminitis": [
        "Withhold grain/concentrates immediately and contact an equine veterinarian without delay.",
        "Keep the horse calm in a deeply bedded, safe stall and prevent violent rolling if possible.",
        "Avoid giving unprescribed painkillers before veterinary examination.",
    ],
    "swine_fever_signs": [
        "Strictly isolate affected pigs and halt all farm visits, equipment sharing, and animal movement.",
        "Report suspected Classical or African Swine Fever immediately to veterinary authorities (notifiable disease).",
        "Disinfect pens, boots, and vehicles thoroughly with approved virucidal disinfectants.",
    ],
    "newcastle_poultry_disease": [
        "Quarantine sick birds immediately and separate them from the rest of the flock.",
        "Report suspected Newcastle Disease (Ranikhet) or sudden flock mortality to local veterinary authorities.",
        "Disinfect feeders, drinkers, and coops, and maintain strict biosecurity and routine poultry vaccination.",
    ],
    "canine_parvovirus_signs": [
        "Seek immediate veterinary care—severe vomiting and bloody diarrhea cause rapid dehydration in dogs.",
        "Isolate the dog strictly from other dogs, especially unvaccinated puppies.",
        "Disinfect contaminated surfaces with a vet-recommended bleach solution and review vaccination records.",
    ],
    "feline_upper_respiratory": [
        "Keep the cat warm, calm, and separated from other cats to reduce spread.",
        "Gently wipe eye and nasal discharge with a clean damp cloth and encourage hydration.",
        "Consult a veterinarian—especially if the cat stops eating for more than 24 hours or struggles to breathe.",
    ],
    "rabbit_ear_mites_gi_stasis": [
        "Contact a rabbit-savvy veterinarian promptly—reduced appetite or stopped droppings in rabbits is an emergency.",
        "Provide unlimited fresh hay, clean water, and clean dry bedding.",
        "Separate affected rabbits if ear crusts or mites are suspected to prevent spread.",
    ],
    "dermatological_skin_condition": [
        "Keep bedding clean and dry, and prevent scratching or biting at open sores.",
        "Separate the animal from other pets or livestock in case of contagious mites or fungal infection.",
        "Consult a veterinarian for skin scraping or targeted dermatological examination.",
    ],
    "respiratory_enteric_infection": [
        "Ensure constant access to clean drinking water to prevent dehydration.",
        "Keep the animal in a warm, draft-free, well-ventilated shelter away from healthy animals.",
        "Seek veterinary evaluation promptly if fever, coughing, or diarrhea persists.",
    ],
    "healthy": [
        "Provide balanced nutrition, clean drinking water, and dry, well-ventilated shelter daily.",
        "Keep an updated species-appropriate vaccination and deworming calendar with a veterinarian.",
        "Monitor appetite, body temperature, posture, and coat/feather condition routinely.",
    ],
    "inconclusive": [
        "Separate the animal from healthy herd mates or other pets as a precaution.",
        "Provide clean water, comfortable shelter, and monitor closely for worsening symptoms.",
        "Consult a qualified veterinarian for physical examination.",
    ],
}

INITIAL_ANIMALS: List[Dict[str, Any]] = [
    {
        "slug": "cow",
        "name": "Cow",
        "emoji": "🐄",
        "category": "livestock",
        "ai_supported": True,
        "badge": "Demo Image + Full Symptom Screening",
        "details": "MobileNetV2 demo image classifier (LSD/FMD/Healthy, unvalidated) plus weighted cattle symptom rules.",
    },
    {
        "slug": "buffalo",
        "name": "Buffalo",
        "emoji": "🐃",
        "category": "livestock",
        "ai_supported": True,
        "badge": "Demo Image + Full Symptom Screening",
        "details": "MobileNetV2 demo image classifier (LSD/FMD/Healthy, unvalidated) plus weighted buffalo symptom rules.",
    },
    {
        "slug": "goat",
        "name": "Goat",
        "emoji": "🐐",
        "category": "livestock",
        "ai_supported": False,
        "badge": "Photo Attach + Symptom Screening",
        "details": "Covers PPR, Foot-and-Mouth Disease, Mastitis, respiratory/enteric and skin screening with photo attachment.",
    },
    {
        "slug": "sheep",
        "name": "Sheep",
        "emoji": "🐑",
        "category": "livestock",
        "ai_supported": False,
        "badge": "Photo Attach + Symptom Screening",
        "details": "Covers PPR, Foot-and-Mouth Disease, Mastitis, lameness and respiratory/enteric screening with photo attachment.",
    },
    {
        "slug": "horse",
        "name": "Horse",
        "emoji": "🐎",
        "category": "livestock",
        "ai_supported": False,
        "badge": "Photo Attach + Symptom Screening",
        "details": "Covers equine colic/laminitis warning signs, respiratory distress and skin conditions with photo attachment.",
    },
    {
        "slug": "pig",
        "name": "Pig",
        "emoji": "🐖",
        "category": "livestock",
        "ai_supported": False,
        "badge": "Photo Attach + Symptom Screening",
        "details": "Covers swine fever warning signs, FMD lesions, respiratory/enteric and skin screening with photo attachment.",
    },
    {
        "slug": "chicken",
        "name": "Chicken",
        "emoji": "🐔",
        "category": "poultry",
        "ai_supported": False,
        "badge": "Photo Attach + Symptom Screening",
        "details": "Covers Newcastle Disease (Ranikhet), respiratory/enteric signs and flock red flags with photo attachment.",
    },
    {
        "slug": "dog",
        "name": "Dog",
        "emoji": "🐕",
        "category": "pet",
        "ai_supported": False,
        "badge": "Photo Attach + Symptom Screening",
        "details": "Covers canine parvovirus warning signs, skin/ectoparasitic irritation and respiratory screening with photo attachment.",
    },
    {
        "slug": "cat",
        "name": "Cat",
        "emoji": "🐈",
        "category": "pet",
        "ai_supported": False,
        "badge": "Photo Attach + Symptom Screening",
        "details": "Covers feline upper respiratory infection (URI), skin/coat issues and enteric distress with photo attachment.",
    },
    {
        "slug": "rabbit",
        "name": "Rabbit",
        "emoji": "🐇",
        "category": "pet",
        "ai_supported": False,
        "badge": "Photo Attach + Symptom Screening",
        "details": "Covers ear mites/head tilt, GI stasis emergency indicators and respiratory signs with photo attachment.",
    },
]

_ALL_LIST = ["cow", "buffalo", "goat", "sheep", "horse", "pig", "chicken", "dog", "cat", "rabbit"]
_MAMMALS = ["cow", "buffalo", "goat", "sheep", "horse", "pig", "dog", "cat", "rabbit"]

SYMPTOM_CATALOG: List[Dict[str, Any]] = [
    # General clinical signs
    {
        "id": "fever",
        "label": "Fever (High body temperature)",
        "category": "general",
        "animals": _ALL_LIST,
    },
    {
        "id": "loss_of_appetite",
        "label": "Loss of appetite (Reduced feed intake)",
        "category": "general",
        "animals": _ALL_LIST,
    },
    {
        "id": "coughing",
        "label": "Coughing, sneezing, or respiratory distress",
        "category": "general",
        "animals": _ALL_LIST,
    },
    {
        "id": "diarrhea",
        "label": "Diarrhea or watery droppings",
        "category": "general",
        "animals": _ALL_LIST,
    },
    {
        "id": "skin_lesions",
        "label": "Skin lesions, sores, scabs, or skin redness",
        "category": "general",
        "animals": _MAMMALS,
    },
    {
        "id": "swelling",
        "label": "Swelling (limbs, joints, brisket, or lymph nodes)",
        "category": "general",
        "animals": _MAMMALS,
    },
    {
        "id": "weakness",
        "label": "Weakness / lethargy / depression",
        "category": "general",
        "animals": _ALL_LIST,
    },
    {
        "id": "difficulty_walking",
        "label": "Difficulty walking / lameness / stiff gait",
        "category": "general",
        "animals": _ALL_LIST,
    },
    # Species-specific & hallmark clinical signs
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
        "label": "Blisters / vesicles on tongue, gums, muzzle, snout, or hooves",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep", "pig"],
    },
    {
        "id": "excessive_salivation",
        "label": "Excessive ropy salivation / drooling",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep", "horse", "pig", "dog", "cat"],
    },
    {
        "id": "nasal_ocular_discharge",
        "label": "Nasal and ocular (watery/crusty eye) discharge",
        "category": "specific",
        "animals": _ALL_LIST,
    },
    {
        "id": "swollen_hot_udder",
        "label": "Swollen, hot, painful udder or watery/clotted milk",
        "category": "specific",
        "animals": ["cow", "buffalo", "goat", "sheep"],
    },
    {
        "id": "mouth_ulcers_ppr",
        "label": "Foul-smelling mouth sores / necrotic gums with thick eye-nose discharge",
        "category": "specific",
        "animals": ["goat", "sheep"],
    },
    {
        "id": "abdominal_pain_rolling",
        "label": "Pawing, flank watching, sweating, or repeatedly rolling (colic signs)",
        "category": "specific",
        "animals": ["horse"],
    },
    {
        "id": "skin_red_purple_patches",
        "label": "Red or purplish skin discoloration on ears, belly, or snout",
        "category": "specific",
        "animals": ["pig"],
    },
    {
        "id": "ruffled_feathers_drooping",
        "label": "Ruffled feathers, drooping wings, or swollen comb/wattles",
        "category": "specific",
        "animals": ["chicken"],
    },
    {
        "id": "twisted_neck_paralysis",
        "label": "Twisted neck (torticollis), wing/leg paralysis, or sudden flock mortality",
        "category": "specific",
        "animals": ["chicken"],
    },
    {
        "id": "fur_hair_loss",
        "label": "Patchy hair/fur loss, dandruff, or frequent scratching",
        "category": "specific",
        "animals": ["dog", "cat", "rabbit", "horse"],
    },
    {
        "id": "vomiting",
        "label": "Repeated vomiting or retching",
        "category": "specific",
        "animals": ["dog", "cat", "pig"],
    },
    {
        "id": "bloody_diarrhea",
        "label": "Bloody or foul-smelling dark diarrhea (Urgent red flag)",
        "category": "specific",
        "animals": ["dog", "cat", "pig", "cow", "buffalo", "goat", "sheep", "chicken"],
    },
    {
        "id": "head_tilt_ear_crusts",
        "label": "Crusty/scabby ears, frequent head shaking, or head tilt",
        "category": "specific",
        "animals": ["rabbit", "dog", "cat"],
    },
    {
        "id": "stopped_droppings",
        "label": "Very small or absent fecal pellets / hunched posture",
        "category": "specific",
        "animals": ["rabbit"],
    },
    {
        "id": "unable_to_stand",
        "label": "Unable to stand or sudden collapse (Urgent red flag)",
        "category": "specific",
        "animals": _ALL_LIST,
    },
]

INITIAL_DISEASES: List[Dict[str, Any]] = [
    {
        "slug": "lumpy_skin_disease",
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
        "prevention": CONDITION_PREVENTION["lumpy_skin_disease"],
    },
    {
        "slug": "foot_and_mouth_disease",
        "name": "Foot-and-Mouth Disease (FMD)",
        "affected_animals": "Cow, Buffalo, Goat, Sheep, Pig",
        "ai_supported": True,
        "symptoms": [
            "High fever followed by blister-like vesicles on the tongue, gums, muzzle, snout, and hooves",
            "Excessive ropy salivation and smacking of lips",
            "Lameness, reluctance to stand, or difficulty walking due to hoof lesions",
            "Severe loss of appetite and sudden reduction in milk yield",
        ],
        "causes": "Caused by an Aphthovirus (family Picornaviridae). Spreads rapidly through direct contact with infected animals, contaminated feed, footwear, or aerosols.",
        "prevention": CONDITION_PREVENTION["foot_and_mouth_disease"],
    },
    {
        "slug": "bovine_mastitis",
        "name": "Mastitis (Udder Infection)",
        "affected_animals": "Cow, Buffalo, Goat, Sheep",
        "ai_supported": False,
        "symptoms": [
            "Swollen, hot, painful udder quarters",
            "Watery, clotted, flaky, or blood-tinged milk",
            "Sharp drop in milk output and fever in acute cases",
        ],
        "causes": "Bacterial infection of the mammary gland, often introduced through contaminated milking equipment, wet bedding, or teat injuries.",
        "prevention": CONDITION_PREVENTION["bovine_mastitis"],
    },
    {
        "slug": "ppr_small_ruminants",
        "name": "Peste des Petits Ruminants (PPR / Goat Plague)",
        "affected_animals": "Goat, Sheep",
        "ai_supported": False,
        "symptoms": [
            "Sudden high fever with watery-to-thick eye and nasal discharge",
            "Foul-smelling mouth sores and necrotic gum lesions",
            "Severe diarrhea, coughing, and depression",
        ],
        "causes": "Highly contagious Morbillivirus spread by close contact and respiratory droplets among goats and sheep.",
        "prevention": CONDITION_PREVENTION["ppr_small_ruminants"],
    },
    {
        "slug": "equine_colic_laminitis",
        "name": "Equine Colic / Laminitis Signs",
        "affected_animals": "Horse",
        "ai_supported": False,
        "symptoms": [
            "Pawing, looking at flanks, sweating, or repeatedly rolling",
            "Reluctance to walk, shifting weight between hooves, or stiff gait",
            "Loss of appetite and restlessness",
        ],
        "causes": "Digestive gas, impaction, sudden diet changes, dehydration, or metabolic/hoof inflammation.",
        "prevention": CONDITION_PREVENTION["equine_colic_laminitis"],
    },
    {
        "slug": "swine_fever_signs",
        "name": "Swine Fever (CSF / ASF Warning Signs)",
        "affected_animals": "Pig",
        "ai_supported": False,
        "symptoms": [
            "High fever, weakness, and huddling together",
            "Red or purplish skin discoloration on ears, snout, or abdomen",
            "Vomiting, bloody diarrhea, and difficulty walking",
        ],
        "causes": "Highly contagious viral diseases transmitted via infected pigs, contaminated pork products, equipment, or ticks.",
        "prevention": CONDITION_PREVENTION["swine_fever_signs"],
    },
    {
        "slug": "newcastle_poultry_disease",
        "name": "Newcastle Disease (Ranikhet)",
        "affected_animals": "Chicken",
        "ai_supported": False,
        "symptoms": [
            "Ruffled feathers, drooping wings, and sharp drop in feed intake",
            "Gasping, coughing, or nasal discharge",
            "Greenish watery diarrhea, twisted neck (torticollis), or wing/leg paralysis",
        ],
        "causes": "Avian orthoavulavirus spread through droppings, respiratory secretions, contaminated feed, footwear, and wild birds.",
        "prevention": CONDITION_PREVENTION["newcastle_poultry_disease"],
    },
    {
        "slug": "canine_parvovirus_signs",
        "name": "Canine Parvovirus / Acute Gastroenteritis Signs",
        "affected_animals": "Dog",
        "ai_supported": False,
        "symptoms": [
            "Severe, foul-smelling or bloody diarrhea",
            "Repeated vomiting and rapid dehydration",
            "Extreme lethargy, fever, and loss of appetite",
        ],
        "causes": "Highly contagious canine parvovirus (most severe in unvaccinated puppies), spread via contaminated feces, soil, and bowls.",
        "prevention": CONDITION_PREVENTION["canine_parvovirus_signs"],
    },
    {
        "slug": "feline_upper_respiratory",
        "name": "Feline Upper Respiratory Infection (URI)",
        "affected_animals": "Cat",
        "ai_supported": False,
        "symptoms": [
            "Frequent sneezing, coughing, and watery or thick nasal/eye discharge",
            "Reduced appetite due to congested sense of smell",
            "Fever and lethargy",
        ],
        "causes": "Commonly caused by Feline Herpesvirus (FHV-1) or Feline Calicivirus, spread through direct contact or shared bowls/litter.",
        "prevention": CONDITION_PREVENTION["feline_upper_respiratory"],
    },
    {
        "slug": "rabbit_ear_mites_gi_stasis",
        "name": "Rabbit GI Stasis & Ear Mite Indicators",
        "affected_animals": "Rabbit",
        "ai_supported": False,
        "symptoms": [
            "Very small or absent fecal pellets and hunched posture (GI stasis emergency)",
            "Refusal to eat hay or treats and lethargy",
            "Crusty/scabby ears, scratching, or head tilt (ear mites / infection)",
        ],
        "causes": "Low-fiber diets, stress, dehydration, dental pain, or contagious Psoroptes ear mites.",
        "prevention": CONDITION_PREVENTION["rabbit_ear_mites_gi_stasis"],
    },
    {
        "slug": "healthy",
        "name": "Healthy Animal Baseline",
        "affected_animals": "All 10 Supported Animals",
        "ai_supported": True,
        "symptoms": [
            "Clean coat/feathers free of nodules, crusts, scabs, or open sores",
            "Normal body temperature, alert posture, and steady gait",
            "Regular appetite, normal droppings, and steady output",
        ],
        "causes": "Good nutrition, clean housing, regular vaccination, and routine veterinary care.",
        "prevention": CONDITION_PREVENTION["healthy"],
    },
]
