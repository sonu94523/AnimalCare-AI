/**
 * Clearly marked offline fallback data used ONLY when the Flask backend
 * (/api/animals, /api/symptoms, /api/diseases) cannot be reached.
 * The backend's `backend/domain_data.py` is the canonical source of truth.
 */

export const OFFLINE_FALLBACK_ANIMALS = [
  {
    id: 'cow',
    name: 'Cow',
    emoji: '🐄',
    aiSupported: true,
    badge: 'Demo Image + Symptom Screening',
    details: 'Supports MobileNetV2 demo image screening (not clinically validated) and rule-based symptom analysis.'
  },
  {
    id: 'buffalo',
    name: 'Buffalo',
    emoji: '🐃',
    aiSupported: true,
    badge: 'Demo Image + Symptom Screening',
    details: 'Supports MobileNetV2 demo image screening (not clinically validated) and rule-based symptom analysis.'
  },
  {
    id: 'goat',
    name: 'Goat',
    emoji: '🐐',
    aiSupported: false,
    badge: 'AI Image Detection Unavailable',
    details: 'AI image detection is disabled until a verified goat disease image dataset is trained.'
  },
  {
    id: 'sheep',
    name: 'Sheep',
    emoji: '🐑',
    aiSupported: false,
    badge: 'AI Image Detection Unavailable',
    details: 'AI image detection is disabled until a verified sheep disease image dataset is trained.'
  },
  {
    id: 'dog',
    name: 'Dog',
    emoji: '🐕',
    aiSupported: false,
    badge: 'AI Image Detection Unavailable',
    details: 'AI image detection is disabled until a verified canine disease image dataset is trained.'
  },
  {
    id: 'cat',
    name: 'Cat',
    emoji: '🐈',
    aiSupported: false,
    badge: 'AI Image Detection Unavailable',
    details: 'AI image detection is disabled until a verified feline disease image dataset is trained.'
  }
]

export const OFFLINE_FALLBACK_SYMPTOMS = [
  { id: 'fever', label: 'Fever (High body temperature)', category: 'general', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'loss_of_appetite', label: 'Loss of appetite (Reduced feed intake)', category: 'general', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'coughing', label: 'Coughing or respiratory distress', category: 'general', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'diarrhea', label: 'Diarrhea', category: 'general', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'skin_lesions', label: 'Skin lesions / sores / scabs', category: 'general', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'swelling', label: 'Swelling (limbs, brisket, or lymph nodes)', category: 'general', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'weakness', label: 'Weakness / lethargy', category: 'general', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'difficulty_walking', label: 'Difficulty walking / lameness', category: 'general', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'reduced_milk', label: 'Reduced milk production', category: 'specific', animals: ['cow', 'buffalo', 'goat', 'sheep'] },
  { id: 'skin_nodules', label: 'Firm round skin nodules (2–5 cm) on head, neck, or body', category: 'specific', animals: ['cow', 'buffalo'] },
  { id: 'mouth_hoof_blisters', label: 'Blisters / vesicles on tongue, gums, muzzle, or hooves', category: 'specific', animals: ['cow', 'buffalo', 'goat', 'sheep'] },
  { id: 'excessive_salivation', label: 'Excessive ropy salivation / drooling', category: 'specific', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'nasal_ocular_discharge', label: 'Nasal and ocular (watery eye) discharge', category: 'specific', animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat'] },
  { id: 'fur_hair_loss', label: 'Patchy hair/fur loss or frequent scratching', category: 'specific', animals: ['dog', 'cat'] }
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
      'Loss of appetite and sharp drop in milk production',
      'Nasal and ocular discharge'
    ],
    causes:
      'Caused by the Lumpy Skin Disease virus (Capripoxvirus), primarily spread by blood-feeding insect vectors such as mosquitoes, biting flies, and ticks.',
    prevention: [
      'Isolate affected cattle immediately from the rest of the herd.',
      'Report suspected cases promptly to local veterinary authorities (LSD is a notifiable livestock disease).',
      'Control blood-feeding insect vectors (mosquitoes, biting flies, ticks) in sheds and follow regional vaccination schedules.',
      'Disinfect premises and avoid sharing needles or equipment between animals.'
    ]
  },
  {
    id: 'foot_and_mouth_disease',
    name: 'Foot-and-Mouth Disease (FMD)',
    affectedAnimals: 'Cow, Buffalo (also affects cloven-hoofed animals like Goat and Sheep)',
    aiSupported: true,
    symptoms: [
      'High fever followed by blister-like vesicles on the tongue, gums, muzzle, and hooves',
      'Excessive ropy salivation and smacking of lips',
      'Lameness, reluctance to stand, or difficulty walking due to hoof lesions',
      'Severe loss of appetite and sudden reduction in milk yield'
    ],
    causes:
      'Caused by an Aphthovirus (family Picornaviridae). Spreads rapidly through direct contact with infected animals, contaminated feed, footwear, or aerosols.',
    prevention: [
      'Report suspected cases immediately to local veterinary authorities (FMD is a WOAH-listed notifiable disease).',
      'Strictly quarantine affected animals and halt livestock movement to prevent spread.',
      'Sanitize footbaths, sheds, footwear, and feeding troughs regularly.',
      'Provide soft, easily consumable feed and clean water while awaiting a veterinary officer.'
    ]
  },
  {
    id: 'healthy',
    name: 'Healthy Animal Baseline',
    affectedAnimals: 'Cow, Buffalo',
    aiSupported: true,
    symptoms: [
      'Clear coat and skin free of nodules, scabs, or open sores',
      'Normal body temperature, alert posture, and steady gait',
      'Regular appetite, rumination, and consistent milk output'
    ],
    causes: 'Good nutrition, clean housing, regular vaccination, and routine veterinary care.',
    prevention: [
      'Provide balanced fodder, clean drinking water, and dry, well-ventilated shelter daily.',
      'Keep an updated vaccination and deworming calendar for LSD and FMD with a veterinarian.',
      'Monitor appetite, body temperature, coat condition, and milk output routinely.'
    ]
  }
]
