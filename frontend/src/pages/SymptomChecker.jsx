import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { ANIMALS } from './AnimalSelection'
import { fetchSymptoms, submitSymptomForm } from '../services/api'

export const SYMPTOM_LIST = [
  {
    id: 'fever',
    label: 'Fever (High body temperature)',
    category: 'general',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'loss_of_appetite',
    label: 'Loss of appetite (Reduced feed intake)',
    category: 'general',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'coughing',
    label: 'Coughing or respiratory distress',
    category: 'general',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'diarrhea',
    label: 'Diarrhea',
    category: 'general',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'skin_lesions',
    label: 'Skin lesions / sores / scabs',
    category: 'general',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'swelling',
    label: 'Swelling (limbs, brisket, or lymph nodes)',
    category: 'general',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'weakness',
    label: 'Weakness / lethargy',
    category: 'general',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'difficulty_walking',
    label: 'Difficulty walking / lameness',
    category: 'general',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'reduced_milk',
    label: 'Reduced milk production',
    category: 'specific',
    animals: ['cow', 'buffalo', 'goat', 'sheep']
  },
  {
    id: 'skin_nodules',
    label: 'Firm round skin nodules (2–5 cm) on head, neck, or body',
    category: 'specific',
    animals: ['cow', 'buffalo']
  },
  {
    id: 'mouth_hoof_blisters',
    label: 'Blisters / vesicles on tongue, gums, muzzle, or hooves',
    category: 'specific',
    animals: ['cow', 'buffalo', 'goat', 'sheep']
  },
  {
    id: 'excessive_salivation',
    label: 'Excessive ropy salivation / drooling',
    category: 'specific',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'nasal_ocular_discharge',
    label: 'Nasal and ocular (watery eye) discharge',
    category: 'specific',
    animals: ['cow', 'buffalo', 'goat', 'sheep', 'dog', 'cat']
  },
  {
    id: 'fur_hair_loss',
    label: 'Patchy hair/fur loss or frequent scratching',
    category: 'specific',
    animals: ['dog', 'cat']
  }
]

function SymptomChecker() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const initialAnimal = searchParams.get('animal') || 'cow'
  const [animalId, setAnimalId] = useState(initialAnimal)
  const [allSymptoms, setAllSymptoms] = useState(SYMPTOM_LIST)
  const [selectedSymptoms, setSelectedSymptoms] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let mounted = true
    fetchSymptoms()
      .then((data) => {
        if (mounted && Array.isArray(data) && data.length > 0) {
          setAllSymptoms(data)
        }
      })
      .catch(() => {
        // Fallback to SYMPTOM_LIST
      })
    return () => {
      mounted = false
    }
  }, [])

  const currentAnimal = ANIMALS.find((a) => a.id === animalId) || ANIMALS[0]

  // Filter symptoms applicable to the selected animal
  const availableSymptoms = allSymptoms.filter(
    (s) => !Array.isArray(s.animals) || s.animals.includes(currentAnimal.id)
  )
  const generalSymptoms = availableSymptoms.filter((s) => s.category !== 'specific')
  const specificSymptoms = availableSymptoms.filter((s) => s.category === 'specific')

  // Remove any selected symptom that is not applicable when switching animals
  useEffect(() => {
    const allowedLabels = new Set(availableSymptoms.map((s) => s.label))
    setSelectedSymptoms((prev) => prev.filter((label) => allowedLabels.has(label)))
  }, [animalId, allSymptoms])

  const toggleSymptom = (symptomLabel) => {
    setErrorMsg('')
    setSelectedSymptoms((prev) =>
      prev.includes(symptomLabel) ? prev.filter((s) => s !== symptomLabel) : [...prev, symptomLabel]
    )
  }

  const handleAnalyzeSymptoms = async (e) => {
    e.preventDefault()
    setErrorMsg('')

    if (!currentAnimal) {
      setErrorMsg('Please select a valid animal category.')
      return
    }

    if (selectedSymptoms.length === 0) {
      setErrorMsg('Form validation error: Please select at least one observed symptom.')
      return
    }

    setSubmitting(true)
    try {
      const response = await submitSymptomForm(currentAnimal.id, selectedSymptoms)
      navigate('/results', {
        state: {
          animal: currentAnimal.name,
          animalId: currentAnimal.id,
          imageName: null,
          previewUrl: null,
          imagePrediction: currentAnimal.aiSupported
            ? 'No image uploaded (Symptom-only check)'
            : `AI Image Detection unavailable for ${currentAnimal.name}`,
          confidence: null,
          symptoms: response.selectedSymptoms || selectedSymptoms,
          symptomAnalysis: response.symptomAnalysis
        }
      })
    } catch (err) {
      const serverErr = err?.response?.data?.error
      if (serverErr) {
        setErrorMsg(serverErr)
      } else {
        // If backend is offline, still allow local demo navigation
        navigate('/results', {
          state: {
            animal: currentAnimal.name,
            animalId: currentAnimal.id,
            imageName: null,
            previewUrl: null,
            imagePrediction: currentAnimal.aiSupported
              ? 'No image uploaded (Symptom-only check)'
              : `AI Image Detection unavailable for ${currentAnimal.name}`,
            confidence: null,
            symptoms: selectedSymptoms,
            symptomAnalysis: `Recorded ${selectedSymptoms.length} symptom(s) for ${currentAnimal.name}.`
          }
        })
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Symptom-Based Disease Checker</h1>
        <p>
          Select an animal and check all observed clinical symptoms. Both general and animal-specific symptoms are provided below.
        </p>
      </div>

      <form className="form-card" onSubmit={handleAnalyzeSymptoms}>
        <div className="form-group">
          <label htmlFor="symptom-animal-select">1. Select Animal Category</label>
          <select
            id="symptom-animal-select"
            className="form-select"
            value={animalId}
            onChange={(e) => {
              setAnimalId(e.target.value)
              setErrorMsg('')
            }}
          >
            {ANIMALS.map((a) => (
              <option key={a.id} value={a.id}>
                {a.emoji} {a.name} ({a.aiSupported ? 'AI + Symptom Check' : 'Symptom Reference Only'})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>2. General Clinical Symptoms</label>
          <div className="symptom-checkbox-grid">
            {generalSymptoms.map((symptom) => {
              const checked = selectedSymptoms.includes(symptom.label)
              return (
                <label
                  key={symptom.id}
                  className={`symptom-checkbox-item ${checked ? 'symptom-checked' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleSymptom(symptom.label)}
                  />
                  <span>{symptom.label}</span>
                </label>
              )
            })}
          </div>
        </div>

        {specificSymptoms.length > 0 && (
          <div className="form-group">
            <label>
              3. Specific Symptoms for {currentAnimal.emoji} {currentAnimal.name}
            </label>
            <div className="symptom-checkbox-grid">
              {specificSymptoms.map((symptom) => {
                const checked = selectedSymptoms.includes(symptom.label)
                return (
                  <label
                    key={symptom.id}
                    className={`symptom-checkbox-item ${checked ? 'symptom-checked' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleSymptom(symptom.label)}
                    />
                    <span>{symptom.label}</span>
                  </label>
                )
              })}
            </div>
          </div>
        )}

        {/* Selected Symptoms Display Panel */}
        <div className="selected-symptoms-box">
          <div className="selected-symptoms-header">
            <strong>Selected Symptoms ({selectedSymptoms.length}):</strong>
            {selectedSymptoms.length > 0 && (
              <button
                type="button"
                className="link-clear-btn"
                onClick={() => setSelectedSymptoms([])}
              >
                Clear All
              </button>
            )}
          </div>
          {selectedSymptoms.length === 0 ? (
            <p className="result-muted">No symptoms selected yet. Click the checkboxes above to add symptoms.</p>
          ) : (
            <div className="symptom-tags">
              {selectedSymptoms.map((sym) => (
                <span key={sym} className="symptom-tag">
                  {sym}
                  <button
                    type="button"
                    className="tag-remove-btn"
                    onClick={() => toggleSymptom(sym)}
                    aria-label={`Remove ${sym}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {errorMsg && <div className="notice-error">{errorMsg}</div>}

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Submitting Symptoms...' : 'Submit & Analyze Symptoms'}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => {
              setSelectedSymptoms([])
              setErrorMsg('')
            }}
          >
            Reset Form
          </button>
        </div>
      </form>
    </div>
  )
}

export default SymptomChecker
