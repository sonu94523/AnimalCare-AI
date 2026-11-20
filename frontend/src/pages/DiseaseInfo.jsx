import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { OFFLINE_FALLBACK_ANIMALS, OFFLINE_FALLBACK_DISEASES } from '../data/fallbackData'
import { fetchDiseases, fetchModelInfo } from '../services/api'

function DiseaseInfo() {
  const [diseases, setDiseases] = useState(OFFLINE_FALLBACK_DISEASES)
  const [modelInfo, setModelInfo] = useState(null)
  const [animalFilter, setAnimalFilter] = useState('all')
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
        // Fallback to OFFLINE_FALLBACK_DISEASES
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
    const affectedText = (d.affectedAnimals || '').toLowerCase()
    const matchesAnimal =
      animalFilter === 'all' ||
      affectedText.includes(animalFilter) ||
      affectedText.includes('all 10')
    const q = searchTerm.trim().toLowerCase()
    const matchesSearch =
      !q ||
      d.name.toLowerCase().includes(q) ||
      affectedText.includes(q) ||
      (d.causes || '').toLowerCase().includes(q)
    return matchesAnimal && matchesSearch
  })

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Supported Disease & Condition Guide</h1>
        <p>
          Reference guide across all 10 supported animals based on general veterinary literature. No medication dosages or prescriptions are provided.
        </p>
      </div>

      {modelInfo && (
        <div className="form-card" style={{ marginBottom: '1.5rem' }}>
          <div className="model-status-header">
            <h3 style={{ margin: 0 }}>MobileNetV2 Image Model Status</h3>
            <span className="status-pill pill-inactive">
              Not Validated on Real Animals (Demo Only)
            </span>
          </div>
          <p className="result-muted" style={{ marginBottom: '0.75rem' }}>
            Backbone: <strong>{modelInfo.backbone}</strong> | Input:{' '}
            <strong>{(modelInfo.inputShape || [224, 224, 3]).join(' × ')} RGB</strong> | Checkpoint:{' '}
            <strong>{modelInfo.modelLoaded ? 'Loaded' : 'Not Trained Yet'}</strong> | Training Data:{' '}
            <strong>{modelInfo.trainingData || 'synthetic / unverified'}</strong>
          </p>
          <div className="notice-warning" style={{ marginBottom: 0 }}>
            {modelInfo.statusNote ||
              'This image model has not been validated on real animal photographs and must not be used as a clinical diagnosis.'}
          </div>
        </div>
      )}

      <div className="filter-bar">
        <div className="category-tabs">
          <button
            type="button"
            className={`category-tab ${animalFilter === 'all' ? 'active' : ''}`}
            onClick={() => setAnimalFilter('all')}
          >
            All Animals
          </button>
          {OFFLINE_FALLBACK_ANIMALS.map((a) => (
            <button
              key={a.id}
              type="button"
              className={`category-tab ${animalFilter === a.id ? 'active' : ''}`}
              onClick={() => setAnimalFilter(a.id)}
            >
              {a.emoji} {a.name}
            </button>
          ))}
        </div>
        <input
          type="text"
          className="search-input"
          placeholder="Search condition or cause..."
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

      <div className="vet-advisory-box">
        <strong>Important Notice:</strong> Always consult a registered veterinary practitioner for accurate diagnosis and treatment plans.
      </div>

      <div className="form-actions">
        <Link to="/select-animal" className="btn btn-primary">
          Start Health Screening
        </Link>
      </div>
    </div>
  )
}

export default DiseaseInfo
