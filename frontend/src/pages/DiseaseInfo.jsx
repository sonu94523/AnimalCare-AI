import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchDiseases } from '../services/api'

const SUPPORTED_DISEASES = [
  {
    id: 'lsd',
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
      'Follow regional veterinary vaccination schedules against LSD.',
      'Practice vector control (clean drainage, insect repellents, regular shed hygiene).',
      'Disinfect premises and avoid sharing needles or equipment between animals.'
    ]
  },
  {
    id: 'fmd',
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
      'Ensure routine FMD vaccination as recommended by local veterinary authorities.',
      'Strictly quarantine newly introduced or sick animals.',
      'Sanitize footbaths, sheds, and feeding troughs regularly.',
      'Restrict movement of livestock during suspected local outbreaks.'
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
      'Provide balanced fodder and clean drinking water daily.',
      'Maintain dry, well-ventilated shelters.',
      'Keep an updated vaccination and deworming calendar with a veterinarian.'
    ]
  }
]

function DiseaseInfo() {
  const [diseases, setDiseases] = useState(SUPPORTED_DISEASES)

  useEffect(() => {
    let mounted = true
    fetchDiseases()
      .then((data) => {
        if (mounted && Array.isArray(data) && data.length > 0) {
          setDiseases(data)
        }
      })
      .catch(() => {
        // Fallback to SUPPORTED_DISEASES
      })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Supported Disease Information</h1>
        <p>
          Reference guide based on general veterinary literature for conditions screened by AnimalCare AI. No medication dosages or prescriptions are provided.
        </p>
      </div>

      <div className="disease-list">
        {diseases.map((disease) => (
          <div key={disease.id} className="disease-card">
            <div className="disease-card-header">
              <h2>{disease.name}</h2>
              <span className="status-pill pill-active">
                Affected: {disease.affectedAnimals}
              </span>
            </div>

            <div className="disease-sections">
              <div className="disease-block">
                <h4>Common Symptoms</h4>
                <ul className="result-list">
                  {disease.symptoms.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="disease-block">
                <h4>General Causes</h4>
                <p>{disease.causes}</p>
              </div>

              <div className="disease-block">
                <h4>General Prevention & Care</h4>
                <ul className="result-list">
                  {disease.prevention.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="vet-advisory-box" style={{ marginTop: '1.5rem' }}>
        <strong>Important Notice:</strong> Always consult a registered veterinary practitioner for accurate diagnosis and treatment plans.
      </div>

      <div className="form-actions" style={{ marginTop: '1.25rem' }}>
        <Link to="/select-animal" className="btn btn-primary">
          Start Disease Detection
        </Link>
      </div>
    </div>
  )
}

export default DiseaseInfo
