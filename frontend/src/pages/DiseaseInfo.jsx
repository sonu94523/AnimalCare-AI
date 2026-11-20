import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchDiseases, fetchModelInfo } from '../services/api'

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
      'Report suspected cases to local veterinary authorities (notifiable livestock disease).',
      'Follow regional veterinary vaccination schedules against LSD.',
      'Practice vector control (clean drainage, insect repellents, regular shed hygiene).'
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
      'Report suspected cases immediately to local veterinary authorities (WOAH-listed notifiable disease).',
      'Ensure routine FMD vaccination as recommended by local veterinary authorities.',
      'Strictly quarantine newly introduced or sick animals.',
      'Sanitize footbaths, sheds, and feeding troughs regularly.'
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
  const [modelInfo, setModelInfo] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

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

    fetchModelInfo()
      .then((info) => {
        if (mounted && info) {
          setModelInfo(info)
        }
      })
      .catch(() => {
        // Optional model metadata
      })

    return () => {
      mounted = false
    }
  }, [])

  const filteredDiseases = diseases.filter((d) => {
    if (!searchTerm.trim()) return true
    const q = searchTerm.toLowerCase()
    return (
      d.name.toLowerCase().includes(q) ||
      (d.affectedAnimals || '').toLowerCase().includes(q) ||
      (d.causes || '').toLowerCase().includes(q)
    )
  })

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Supported Disease Information</h1>
        <p>
          Reference guide based on general veterinary literature for conditions covered by AnimalCare AI. No medication dosages or prescriptions are provided.
        </p>
      </div>

      {modelInfo && (
        <div className="form-card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.6rem' }}>
            <h3 style={{ margin: 0 }}>MobileNetV2 Image Model Status</h3>
            <span className="status-pill pill-inactive">
              Not Validated on Real Animals (Demo Only)
            </span>
          </div>
          <p className="result-muted" style={{ marginBottom: '0.65rem' }}>
            Backbone: <strong>{modelInfo.backbone}</strong> | Input:{' '}
            <strong>{(modelInfo.inputShape || [224, 224, 3]).join(' × ')} RGB</strong> | Checkpoint:{' '}
            <strong>{modelInfo.modelLoaded ? 'Loaded' : 'Not Trained Yet'}</strong> | Training Data:{' '}
            <strong>{modelInfo.trainingData || 'synthetic / unverified'}</strong>
          </p>
          <div className="notice-warning" style={{ margin: 0 }}>
            {modelInfo.statusNote ||
              'This image model has not been validated on real animal photographs and must not be used as a clinical diagnosis.'}
          </div>
        </div>
      )}

      <div className="form-group" style={{ marginBottom: '1.25rem' }}>
        <input
          type="text"
          className="form-select"
          placeholder="Search condition by name, animal, or cause..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="disease-list">
        {filteredDiseases.map((disease) => (
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
