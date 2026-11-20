import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { OFFLINE_FALLBACK_ANIMALS } from '../data/fallbackData'
import { fetchAnimals } from '../services/api'

export const ANIMALS = OFFLINE_FALLBACK_ANIMALS

const CATEGORY_TABS = [
  { id: 'all', label: 'All (10)' },
  { id: 'livestock', label: 'Livestock' },
  { id: 'poultry', label: 'Poultry' },
  { id: 'pet', label: 'Pets' }
]

function AnimalSelection() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const [animalsList, setAnimalsList] = useState(OFFLINE_FALLBACK_ANIMALS)
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

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

  const paramAnimal = searchParams.get('animal') || 'cow'
  const selectedId = animalsList.some((a) => a.id === paramAnimal) ? paramAnimal : animalsList[0].id
  const setSelectedId = (id) => setSearchParams({ animal: id }, { replace: true })

  const selectedAnimal = animalsList.find((a) => a.id === selectedId) || animalsList[0]

  const filteredAnimals = animalsList.filter((a) => {
    const matchesCategory = categoryFilter === 'all' || (a.category || 'livestock') === categoryFilter
    const matchesSearch =
      !searchQuery.trim() ||
      a.name.toLowerCase().includes(searchQuery.trim().toLowerCase()) ||
      (a.details || '').toLowerCase().includes(searchQuery.trim().toLowerCase())
    return matchesCategory && matchesSearch
  })

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Step 1: Select Animal Category</h1>
        <p>
          Choose any of the 10 supported animals to run photo screening, symptom checking, or combined screening.
        </p>
      </div>

      <div className="filter-bar">
        <div className="category-tabs">
          {CATEGORY_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`category-tab ${categoryFilter === tab.id ? 'active' : ''}`}
              onClick={() => setCategoryFilter(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <input
          type="text"
          className="search-input"
          placeholder="Search animal or condition..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="animal-grid">
        {filteredAnimals.map((animal) => {
          const isSelected = animal.id === selectedId
          return (
            <div
              key={animal.id}
              onClick={() => setSelectedId(animal.id)}
              className={`animal-card selectable-card ${
                animal.aiSupported ? 'animal-supported' : 'animal-unsupported'
              } ${isSelected ? 'card-selected' : ''}`}
            >
              <div>
                <div className="animal-card-top">
                  <span className="animal-emoji">{animal.emoji}</span>
                  <span className={`status-pill ${animal.aiSupported ? 'pill-active' : 'pill-info'}`}>
                    {animal.badge}
                  </span>
                </div>
                <span className="animal-category-tag">{animal.category || 'livestock'}</span>
                <h3>{animal.name}</h3>
                <p>{animal.details}</p>
              </div>
              <button
                type="button"
                className={`btn btn-small btn-block ${isSelected ? 'btn-primary' : 'btn-outline'}`}
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
            Selected: {selectedAnimal.emoji} {selectedAnimal.name}
          </h2>
          {selectedAnimal.aiSupported ? (
            <div className="notice-success" style={{ marginBottom: 0 }}>
              ✓ <strong>Demo Image Classifier + Full Symptom Rules ready</strong> for {selectedAnimal.name}. You can upload a photo, select clinical symptoms, or combine both.
            </div>
          ) : (
            <div className="notice-info" style={{ marginBottom: 0 }}>
              ✓ <strong>Full Symptom Screening + Photo Attachment ready</strong> for {selectedAnimal.name}. Upload a photo for visual quality check & veterinary report attachment, and run species-specific symptom matching.
            </div>
          )}
        </div>

        <div className="summary-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => navigate(`/symptoms?animal=${selectedAnimal.id}`)}
          >
            🩺 Check {selectedAnimal.name} Symptoms
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate(`/image-detection?animal=${selectedAnimal.id}`)}
          >
            📷 {selectedAnimal.aiSupported ? `Demo Image Check (${selectedAnimal.name})` : `Upload ${selectedAnimal.name} Photo`}
          </button>
        </div>
      </div>
    </div>
  )
}

export default AnimalSelection
