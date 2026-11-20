import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { OFFLINE_FALLBACK_ANIMALS } from '../data/fallbackData'
import { fetchAnimals } from '../services/api'

export const ANIMALS = OFFLINE_FALLBACK_ANIMALS

function AnimalSelection() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const initialAnimal = searchParams.get('animal') || 'cow'
  const [animalsList, setAnimalsList] = useState(OFFLINE_FALLBACK_ANIMALS)
  const [selectedId, setSelectedId] = useState(initialAnimal)

  useEffect(() => {
    let mounted = true
    fetchAnimals()
      .then((data) => {
        if (mounted && Array.isArray(data) && data.length > 0) {
          setAnimalsList(data)
        }
      })
      .catch(() => {
        // Fallback to OFFLINE_FALLBACK_ANIMALS when backend is offline
      })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const paramAnimal = searchParams.get('animal')
    if (paramAnimal && animalsList.some((a) => a.id === paramAnimal)) {
      setSelectedId(paramAnimal)
    }
  }, [searchParams, animalsList])

  const selectedAnimal = animalsList.find((a) => a.id === selectedId) || animalsList[0]

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Step 1: Select Animal Category</h1>
        <p>
          Choose an animal below to begin preliminary disease screening. Demo image screening is configured for <strong>Cow</strong> and <strong>Buffalo</strong>.
        </p>
      </div>

      <div className="animal-grid">
        {animalsList.map((animal) => {
          const isSelected = animal.id === selectedId
          return (
            <div
              key={animal.id}
              onClick={() => setSelectedId(animal.id)}
              className={`animal-card selectable-card ${
                animal.aiSupported ? 'animal-supported' : 'animal-unsupported'
              } ${isSelected ? 'card-selected' : ''}`}
            >
              <div className="animal-card-top">
                <span className="animal-emoji">{animal.emoji}</span>
                <span className={`status-pill ${animal.aiSupported ? 'pill-active' : 'pill-inactive'}`}>
                  {animal.badge}
                </span>
              </div>
              <h3>{animal.name}</h3>
              <p>{animal.details}</p>
              <button
                type="button"
                className={`btn btn-small ${isSelected ? 'btn-primary' : 'btn-outline'}`}
                onClick={(e) => {
                  e.stopPropagation()
                  setSelectedId(animal.id)
                }}
              >
                {isSelected ? '✓ Selected' : `Select ${animal.name}`}
              </button>
            </div>
          )
        })}
      </div>

      <div className="selection-summary-card">
        <div className="summary-info">
          <h2>
            Selected Animal: {selectedAnimal.emoji} {selectedAnimal.name}
          </h2>
          {selectedAnimal.aiSupported ? (
            <p className="notice-success">
              ✓ <strong>Demo Image & Symptom Screening available</strong> for {selectedAnimal.name}. You can proceed with image upload, symptom analysis, or both.
            </p>
          ) : (
            <p className="notice-warning">
              ⚠️ <strong>AI Image Detection is currently unavailable</strong> for {selectedAnimal.name}. We never generate fake image predictions for unsupported animals.
            </p>
          )}
        </div>

        <div className="summary-actions">
          {selectedAnimal.aiSupported ? (
            <>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => navigate(`/image-detection?animal=${selectedAnimal.id}`)}
              >
                Proceed to Image Detection
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => navigate(`/symptoms?animal=${selectedAnimal.id}`)}
              >
                Go to Symptom Checker
              </button>
            </>
          ) : (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate(`/symptoms?animal=${selectedAnimal.id}`)}
            >
              Continue to Symptom Checker Only
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default AnimalSelection
