/**
 * Offline fallback data synced with `backend/domain_data.py`.
 * Used only when the Flask backend (/api/animals, /api/symptoms, /api/diseases)
 * cannot be reached. Verified by backend/tests/test_app_and_ml.py.
 */

export const OFFLINE_FALLBACK_ANIMALS = [
  {
    id: 'cow',
    name: 'Cow',
    emoji: '🐄',
    category: 'livestock',
    aiSupported: true,
    badge: 'Demo Image + Full Symptom Screening',
    details: 'MobileNetV2 demo image classifier (LSD/FMD/Healthy, unvalidated) plus weighted cattle symptom rules.'
  },
  {
    id: 'buffalo',
    name: 'Buffalo',
    emoji: '🐃',
    category: 'livestock',
    aiSupported: true,
    badge: 'Demo Image + Full Symptom Screening',
    details: 'MobileNetV2 demo image classifier (LSD/FMD/Healthy, unvalidated) plus weighted buffalo symptom rules.'
  },
  {
    id: 'goat',
    name: 'Goat',
    emoji: '🐐',
    category: 'livestock',
    aiSupported: false,
    badge: 'Photo Attach + Symptom Screening',
    details: 'Covers PPR, Foot-and-Mouth Disease, Mastitis, respiratory/enteric and skin screening with photo attachment.'
  },
  {
    id: 'sheep',
    name: 'Sheep',
    emoji: '🐑',
    category: 'livestock',
    aiSupported: false,
    badge: 'Photo Attach + Symptom Screening',
    details: 'Covers PPR, Foot-and-Mouth Disease, Mastitis, lameness and respiratory/enteric screening with photo attachment.'
  },
  {
    id: 'horse',
    name: 'Horse',
    emoji: '🐎',
    category: 'livestock',
    aiSupported: false,
    badge: 'Photo Attach + Symptom Screening',
    details: 'Covers equine colic/laminitis warning signs, respiratory distress and skin conditions with photo attachment.'
  },
  {
    id: 'pig',
    name: 'Pig',
    emoji: '🐖',
    category: 'livestock',
    aiSupported: false,
    badge: 'Photo Attach + Symptom Screening',
    details: 'Covers swine fever warning signs, FMD lesions, respiratory/enteric and skin screening with photo attachment.'
  },
  {
    id: 'chicken',
    name: 'Chicken',
    emoji: '🐔',
    category: 'poultry',
    aiSupported: false,
    badge: 'Photo Attach + Symptom Screening',
    details: 'Covers Newcastle Disease (Ranikhet), respiratory/enteric signs and flock red flags with photo attachment.'
  },
  {
    id: 'dog',
    name: 'Dog',
    emoji: '🐕',
    category: 'pet',
    aiSupported: false,
    badge: 'Photo Attach + Symptom Screening',
    details: 'Covers canine parvovirus warning signs, skin/ectoparasitic irritation and respiratory screening with photo attachment.'
  },
  {
    id: 'cat',
    name: 'Cat',
    emoji: '🐈',
    category: 'pet',
    aiSupported: false,
    badge: 'Photo Attach + Symptom Screening',
    details: 'Covers feline upper respiratory infection (URI), skin/coat issues and enteric distress with photo attachment.'
  },
  {
    id: 'rabbit',
    name: 'Rabbit',
    emoji: '🐇',
    category: 'pet',
    aiSupported: false,
    badge: 'Photo Attach + Symptom Screening',
    details: 'Covers ear mites/head tilt, GI stasis emergency indicators and respiratory signs with photo attachment.'
  }
]

const ALL_TEN = ['cow', 'buffalo', 'goat', 'sheep', 'horse', 'pig', 'chicken', 'dog', 'cat', 'rabbit']
const MAMMALS = ['cow', 'buffalo', 'goat', 'sheep', 'horse', 'pig', 'dog', 'cat', 'rabbit']

export const OFFLINE_FALLBACK_SYMPTOMS = [
  { id: 'fever', label: 'Fever (High body temperature)', category: 'general', animals: ALL_TEN },
  { id: 'loss_of_appetite', label: 'Loss of appetite (Reduced feed intake)', category: 'general', animals: ALL_TEN },
  { id: 'coughing', label: 'Coughing, sneezing, or respiratory distress', category: 'general', animals: ALL_TEN },
  { id: 'diarrhea', label: 'Diarrhea or watery droppings', category: 'general', animals: ALL_TEN },
  { id: 'skin_lesions', label: 'Skin lesions, sores, scabs, or skin redness', category: 'general', animals: MAMMALS },
  { id: 'swelling', label: 'Swelling (limbs, joints, brisket, or lymph nodes)', category: 'general', animals: MAMMALS },
  { id: 'weakness', label: 'Weakness / lethargy / depression', category: 'general', animals: ALL_TEN },
  { id: 'difficulty_walking', label: 'Difficulty walking / lameness / stiff gait', category: 'general', animals: ALL_TEN },
  { id: 'reduced_milk', label: 'Reduced milk production', category: 'specific', animals: ['cow', 'buffalo', 'goat', 'sheep'] },
  { id: 'skin_nodules', label: 'Firm round skin nodules (2–5 cm) on head, neck, or body', category: 'specific', animals: ['cow', 'buffalo'] },
  { id: 'mouth_hoof_blisters', label: 'Blisters / vesicles on tongue, gums, muzzle, snout, or hooves', category: 'specific', animals: ['cow', 'buffalo', 'goat', 'sheep', 'pig'] },
  { id: 'excessive_salivation', label: 'Excessive ropy salivation / drooling', category: 'specific', animals: ['cow', 'buffalo', 'goat', 'sheep', 'horse', 'pig', 'dog', 'cat'] },
  { id: 'nasal_ocular_discharge', label: 'Nasal and ocular (watery/crusty eye) discharge', category: 'specific', animals: ALL_TEN },
  { id: 'swollen_hot_udder', label: 'Swollen, hot, painful udder or watery/clotted milk', category: 'specific', animals: ['cow', 'buffalo', 'goat', 'sheep'] },
  { id: 'mouth_ulcers_ppr', label: 'Foul-smelling mouth sores / necrotic gums with thick eye-nose discharge', category: 'specific', animals: ['goat', 'sheep'] },
  { id: 'abdominal_pain_rolling', label: 'Pawing, flank watching, sweating, or repeatedly rolling (colic signs)', category: 'specific', animals: ['horse'] },
  { id: 'skin_red_purple_patches', label: 'Red or purplish skin discoloration on ears, belly, or snout', category: 'specific', animals: ['pig'] },
  { id: 'ruffled_feathers_drooping', label: 'Ruffled feathers, drooping wings, or swollen comb/wattles', category: 'specific', animals: ['chicken'] },
  { id: 'twisted_neck_paralysis', label: 'Twisted neck (torticollis), wing/leg paralysis, or sudden flock mortality', category: 'specific', animals: ['chicken'] },
  { id: 'fur_hair_loss', label: 'Patchy hair/fur loss, dandruff, or frequent scratching', category: 'specific', animals: ['dog', 'cat', 'rabbit', 'horse'] },
  { id: 'vomiting', label: 'Repeated vomiting or retching', category: 'specific', animals: ['dog', 'cat', 'pig'] },
  { id: 'bloody_diarrhea', label: 'Bloody or foul-smelling dark diarrhea (Urgent red flag)', category: 'specific', animals: ['dog', 'cat', 'pig', 'cow', 'buffalo', 'goat', 'sheep', 'chicken'] },
  { id: 'head_tilt_ear_crusts', label: 'Crusty/scabby ears, frequent head shaking, or head tilt', category: 'specific', animals: ['rabbit', 'dog', 'cat'] },
  { id: 'stopped_droppings', label: 'Very small or absent fecal pellets / hunched posture', category: 'specific', animals: ['rabbit'] },
  { id: 'unable_to_stand', label: 'Unable to stand or sudden collapse (Urgent red flag)', category: 'specific', animals: ALL_TEN }
]

export const OFFLINE_FALLBACK_DISEASES = [
  {
    id: 'lumpy_skin_disease',
    name: 'Lumpy Skin Disease (LSD)',
    affectedAnimals: 'Cow, Buffalo',
    aiSupported: true,
    symptoms: [
      'Firm, round skin nodules (2–5 cm) on the head, neck, limbs, and body',
      'High fever (often exceeding 40°C / 104°F)',
      'Swelling of superficial lymph nodes and limbs',
      'Loss of appetite and sharp drop in milk production'
    ],
    causes: 'Caused by Capripoxvirus, primarily spread by biting flies, mosquitoes, and ticks.',
    prevention: [
      'Isolate affected cattle immediately from the rest of the herd.',
      'Report suspected cases promptly to local veterinary authorities.'
    ]
  },
  {
    id: 'foot_and_mouth_disease',
    name: 'Foot-and-Mouth Disease (FMD)',
    affectedAnimals: 'Cow, Buffalo, Goat, Sheep, Pig',
    aiSupported: true,
    symptoms: [
      'Blister-like vesicles on tongue, gums, muzzle, snout, and hooves',
      'Excessive ropy salivation and lameness'
    ],
    causes: 'Caused by an Aphthovirus spreading rapidly via direct contact, feed, or footwear.',
    prevention: [
      'Report suspected cases immediately to local veterinary authorities (WOAH-listed).',
      'Strictly quarantine affected animals and disinfect footbaths and sheds.'
    ]
  },
  {
    id: 'bovine_mastitis',
    name: 'Mastitis (Udder Infection)',
    affectedAnimals: 'Cow, Buffalo, Goat, Sheep',
    aiSupported: false,
    symptoms: ['Swollen, hot, painful udder quarters', 'Watery, clotted, or flaky milk'],
    causes: 'Bacterial infection of the mammary gland.',
    prevention: ['Keep udder and milking area clean and dry; consult a veterinarian promptly.']
  },
  {
    id: 'ppr_small_ruminants',
    name: 'Peste des Petits Ruminants (PPR / Goat Plague)',
    affectedAnimals: 'Goat, Sheep',
    aiSupported: false,
    symptoms: ['High fever with thick eye/nasal discharge', 'Foul mouth sores and diarrhea'],
    causes: 'Contagious Morbillivirus spread among goats and sheep.',
    prevention: ['Isolate sick animals and report suspected PPR to veterinary authorities.']
  },
  {
    id: 'equine_colic_laminitis',
    name: 'Equine Colic / Laminitis Signs',
    affectedAnimals: 'Horse',
    aiSupported: false,
    symptoms: ['Pawing, flank watching, sweating, or rolling', 'Stiff gait or hoof tenderness'],
    causes: 'Digestive impaction/gas, diet change, or metabolic hoof inflammation.',
    prevention: ['Withhold grain and contact an equine veterinarian immediately.']
  },
  {
    id: 'swine_fever_signs',
    name: 'Swine Fever (CSF / ASF Warning Signs)',
    affectedAnimals: 'Pig',
    aiSupported: false,
    symptoms: ['High fever and weakness', 'Red/purplish skin patches on ears or belly'],
    causes: 'Contagious viral disease spread through direct contact or contaminated equipment.',
    prevention: ['Strictly isolate pigs and report immediately to veterinary authorities.']
  },
  {
    id: 'newcastle_poultry_disease',
    name: 'Newcastle Disease (Ranikhet)',
    affectedAnimals: 'Chicken',
    aiSupported: false,
    symptoms: ['Ruffled feathers, drooping wings, gasping', 'Twisted neck or paralysis'],
    causes: 'Avian orthoavulavirus spread through droppings and respiratory droplets.',
    prevention: ['Quarantine sick birds and report sudden mortality to veterinary authorities.']
  },
  {
    id: 'canine_parvovirus_signs',
    name: 'Canine Parvovirus / Acute Gastroenteritis Signs',
    affectedAnimals: 'Dog',
    aiSupported: false,
    symptoms: ['Severe bloody diarrhea and vomiting', 'Extreme lethargy and dehydration'],
    causes: 'Highly contagious canine parvovirus, most severe in unvaccinated puppies.',
    prevention: ['Seek immediate veterinary care and isolate from other dogs.']
  },
  {
    id: 'feline_upper_respiratory',
    name: 'Feline Upper Respiratory Infection (URI)',
    affectedAnimals: 'Cat',
    aiSupported: false,
    symptoms: ['Sneezing, coughing, watery/thick eye and nose discharge', 'Reduced appetite'],
    causes: 'Feline Herpesvirus or Calicivirus spread via contact or shared bowls.',
    prevention: ['Isolate from other cats, keep warm, and consult a veterinarian.']
  },
  {
    id: 'rabbit_ear_mites_gi_stasis',
    name: 'Rabbit GI Stasis & Ear Mite Indicators',
    affectedAnimals: 'Rabbit',
    aiSupported: false,
    symptoms: ['Small or absent droppings and hunched posture', 'Crusty ears or head tilt'],
    causes: 'Low-fiber diet, stress, dental issues, or contagious ear mites.',
    prevention: ['Contact a rabbit-savvy vet urgently for stopped droppings or head tilt.']
  },
  {
    id: 'healthy',
    name: 'Healthy Animal Baseline',
    affectedAnimals: 'All 10 Supported Animals',
    aiSupported: true,
    symptoms: ['Clear coat/feathers', 'Normal appetite, posture, and output'],
    causes: 'Good nutrition, clean housing, and routine veterinary care.',
    prevention: ['Maintain clean water, balanced feed, and routine vaccination schedules.']
  }
]
