import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom'
import { OFFLINE_FALLBACK_ANIMALS, OFFLINE_FALLBACK_SYMPTOMS } from '../data/fallbackData'
import { fetchSymptoms, submitSymptomForm, submitCombinedPrediction } from '../services/api'

export const SYMPTOM_LIST = OFFLINE_FALLBACK_SYMPTOMS

function SymptomChecker() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()
  const attachedImageState = location.state || {}
  const paramAnimal = searchParams.get('animal') || 'cow'
  const [animalId, setAnimalId] = useState(paramAnimal)
  const [allSymptoms, setAllSymptoms] = useState(OFFLINE_FALLBACK_SYMPTOMS)
  const [selectedSymptomIds, setSelectedSymptomIds] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    if (OFFLINE_FALLBACK_ANIMALS.some((a) => a.id === paramAnimal)) {
      setAnimalId(paramAnimal)
    }
  }, [paramAnimal])

  useEffect(() => {
    let mounted = true
    fetchSymptoms()
      .then((data) => {
        if (mounted && Array.isArray(data) && data.length > 0) {
          setAllSymptoms(data)
        }
      })
      .catch(() => {
        // Fallback to OFFLINE_FALLBACK_SYMPTOMS
      })
    return () => {
      mounted = false
    }
  }, [])

  const currentAnimal = OFFLINE_FALLBACK_ANIMALS.find((a) => a.id === animalId) || OFFLINE_FALLBACK_ANIMALS[0]

  const availableSymptoms = allSymptoms.filter(
    (s) => !Array.isArray(s.animals) || s.animals.includes(currentAnimal.id)
  )
  const generalSymptoms = availableSymptoms.filter((s) => s.category !== 'specific')
  const specificSymptoms = availableSymptoms.filter((s) => s.category === 'specific')
  const symptomLabelById = Object.fromEntries(availableSymptoms.map((s) => [s.id, s.label]))

  // Drop selected symptoms that are no longer applicable when switching animals
  useEffect(() => {
    const allowedIds = new Set(availableSymptoms.map((s) => s.id))
    setSelectedSymptomIds((prev) => prev.filter((id) => allowedIds.has(id)))
  }, [animalId, allSymptoms])

  const toggleSymptom = (symptomId) => {
    setErrorMsg('')
    setSelectedSymptomIds((prev) =>
      prev.includes(symptomId) ? prev.filter((s) => s !== symptomId) : [...prev, symptomId]
    )
  }

  const handleAnalyzeSymptoms = async (e) => {
    e.preventDefault()
    setErrorMsg('')

    if (!currentAnimal) {
      setErrorMsg('Please select a valid animal category.')
      return
    }

    if (selectedSymptomIds.length === 0) {
      setErrorMsg('Form validation error: Please select at least one observed symptom.')
      return
    }

    setSubmitting(true)
    try {
      const hasAttachedImage = Boolean(
        attachedImageState.uploadId && currentAnimal.aiSupported
      )

      if (hasAttachedImage) {
        const combinedResp = await submitCombinedPrediction({
          animal: currentAnimal.id,
          symptoms: selectedSymptomIds,
          uploadId: attachedImageState.uploadId
        })
        const imgRes = combinedResp.imageResult || attachedImageState.predictionResult
        const symRes = combinedResp.symptomResult || {}
        const combDec = combinedResp.combinedDecision

        navigate('/results', {
          state: {
            animal: currentAnimal.name,
            animalId: currentAnimal.id,
            imageName: attachedImageState.imageName,
            imagePath: attachedImageState.imagePath || null,
            previewUrl: attachedImageState.previewUrl || null,
            imagePrediction: imgRes.imagePrediction,
            predictedClass: imgRes.predictedClass,
            confidence: imgRes.confidence,
            isLowConfidence: imgRes.isLowConfidence,
            isOutOfDistribution: imgRes.isOutOfDistribution,
            uncertaintyNotice: imgRes.uncertaintyNotice,
            classProbabilities: imgRes.classProbabilities,
            modelValidated: imgRes.modelValidated,
            trainingData: imgRes.trainingData,
            modelStatusNote: imgRes.modelStatusNote,
            symptoms: symRes.selectedSymptoms || selectedSymptomIds.map((id) => symptomLabelById[id] || id),
            symptomTopCondition: symRes.topCondition,
            symptomMatchScore: symRes.matchScorePercent,
            symptomMatchLevel: symRes.matchLevel,
            matchedConditions: symRes.matchedConditions || [],
            symptomAnalysis: symRes.symptomAnalysis,
            preventionTips: combDec?.preventionTips || symRes.preventionTips,
            combinedDecision: combDec
          }
        })
        return
      }

      const response = await submitSymptomForm(currentAnimal.id, selectedSymptomIds)
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
          symptoms: response.selectedSymptoms || selectedSymptomIds.map((id) => symptomLabelById[id] || id),
          symptomTopCondition: response.topCondition,
          symptomMatchScore: response.matchScorePercent,
          symptomMatchLevel: response.matchLevel,
          matchedConditions: response.matchedConditions || [],
          symptomAnalysis: response.symptomAnalysis,
          preventionTips: response.preventionTips,
          combinedDecision: response.combinedDecision
        }
      })
    } catch (err) {
      const serverErr = err?.response?.data?.error
      setErrorMsg(
        serverErr ||
          'Could not reach the Flask backend on port 5000. Start the backend server before submitting symptoms.'
      )
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
        {attachedImageState.uploadId && attachedImageState.predictionResult && currentAnimal.aiSupported && (
          <div className="notice-success" style={{ marginBottom: '1.25rem' }}>
            <strong>✓ Uploaded Image Attached for Combined Screening:</strong>{' '}
            {attachedImageState.imageName || 'Animal photo'} — MobileNetV2 demo output:{' '}
            <strong>{attachedImageState.predictionResult.imagePrediction}</strong> (
            {attachedImageState.predictionResult.confidence}% confidence). Select observed clinical symptoms below to cross-check visual and symptomatic evidence.
          </div>
        )}
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
            {OFFLINE_FALLBACK_ANIMALS.map((a) => (
              <option key={a.id} value={a.id}>
                {a.emoji} {a.name} ({a.aiSupported ? 'Demo Image + Symptom Check' : 'Symptom Reference Only'})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>2. General Clinical Symptoms</label>
          <div className="symptom-checkbox-grid">
            {generalSymptoms.map((symptom) => {
              const checked = selectedSymptomIds.includes(symptom.id)
              return (
                <label
                  key={symptom.id}
                  className={`symptom-checkbox-item ${checked ? 'symptom-checked' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleSymptom(symptom.id)}
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
                const checked = selectedSymptomIds.includes(symptom.id)
                return (
                  <label
                    key={symptom.id}
                    className={`symptom-checkbox-item ${checked ? 'symptom-checked' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleSymptom(symptom.id)}
                    />
                    <span>{symptom.label}</span>
                  </label>
                )
              })}
            </div>
          </div>
        )}

        <div className="selected-symptoms-box">
          <div className="selected-symptoms-header">
            <strong>Selected Symptoms ({selectedSymptomIds.length}):</strong>
            {selectedSymptomIds.length > 0 && (
              <button
                type="button"
                className="link-clear-btn"
                onClick={() => setSelectedSymptomIds([])}
              >
                Clear All
              </button>
            )}
          </div>
          {selectedSymptomIds.length === 0 ? (
            <p className="result-muted">No symptoms selected yet. Click the checkboxes above to add symptoms.</p>
          ) : (
            <div className="symptom-tags">
              {selectedSymptomIds.map((symId) => (
                <span key={symId} className="symptom-tag">
                  {symptomLabelById[symId] || symId}
                  <button
                    type="button"
                    className="tag-remove-btn"
                    onClick={() => toggleSymptom(symId)}
                    aria-label={`Remove ${symptomLabelById[symId] || symId}`}
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
              setSelectedSymptomIds([])
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
