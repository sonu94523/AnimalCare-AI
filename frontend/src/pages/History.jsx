import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  API_BASE_URL,
  fetchAnimals,
  fetchHistory,
  deleteHistoryRecord,
  clearAllHistory
} from '../services/api'
import { OFFLINE_FALLBACK_ANIMALS } from '../data/fallbackData'

export function formatLocalTimestamp(isoOrDate) {
  if (!isoOrDate) return 'N/A'
  const parsed = new Date(isoOrDate)
  if (Number.isNaN(parsed.getTime())) return String(isoOrDate)
  return parsed.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function History() {
  const navigate = useNavigate()
  const [animals, setAnimals] = useState(OFFLINE_FALLBACK_ANIMALS)
  const [records, setRecords] = useState([])
  const [animalFilter, setAnimalFilter] = useState('all')
  const [refreshTick, setRefreshTick] = useState(0)
  const [adminToken, setAdminToken] = useState('')
  const [loading, setLoading] = useState(true)
  const [statusMsg, setStatusMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let active = true
    fetchAnimals()
      .then((data) => {
        if (active && Array.isArray(data) && data.length > 0) {
          setAnimals(data)
        }
      })
      .catch(() => {
        // Fallback to OFFLINE_FALLBACK_ANIMALS
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    fetchHistory(animalFilter)
      .then((data) => {
        if (active) {
          setRecords(Array.isArray(data) ? data : [])
        }
      })
      .catch(() => {
        if (active) {
          setRecords([])
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [animalFilter, refreshTick])

  const ensureAdminToken = () => {
    if (adminToken.trim()) return adminToken.trim()
    const entered = window.prompt('Enter the server ADMIN_TOKEN to modify history:')
    if (entered && entered.trim()) {
      setAdminToken(entered.trim())
      return entered.trim()
    }
    return ''
  }

  const handleDeleteRecord = async (recordId) => {
    if (!window.confirm(`Delete screening record #${recordId}? This cannot be undone.`)) {
      return
    }
    const token = ensureAdminToken()
    if (!token) return

    setErrorMsg('')
    setStatusMsg('')
    try {
      await deleteHistoryRecord(recordId, token)
      setRecords((prev) => prev.filter((r) => r.id !== recordId))
      setStatusMsg(`Deleted screening record #${recordId}.`)
    } catch (err) {
      setErrorMsg(
        err?.response?.data?.error ||
          'Could not delete record. Verify the backend is running and ADMIN_TOKEN matches.'
      )
    }
  }

  const handleClearAll = async () => {
    if (records.length === 0) return
    if (!window.confirm(`Clear ALL ${records.length} saved screening record(s)? This cannot be undone.`)) {
      return
    }
    const token = ensureAdminToken()
    if (!token) return

    setErrorMsg('')
    setStatusMsg('')
    try {
      await clearAllHistory(token)
      setRecords([])
      setStatusMsg('All prediction history records have been cleared.')
    } catch (err) {
      setErrorMsg(
        err?.response?.data?.error ||
          'Could not clear prediction history. Verify the backend is running and ADMIN_TOKEN matches.'
      )
    }
  }

  const handleViewRecord = (rec) => {
    const isValidLocalPath = typeof rec.imagePath === 'string' && rec.imagePath.startsWith('/uploads/')
    const previewUrl = isValidLocalPath ? `${API_BASE_URL}${rec.imagePath}` : null
    const details = rec.details || {}
    const imgRes = details.imageResult || null
    const symRes = details.symptomResult || null
    const combDec = details.combinedDecision || null

    navigate('/results', {
      state: {
        animal: rec.animal,
        animalId: rec.animalId || (rec.animal || 'cow').toLowerCase(),
        imageName: details.originalName || (isValidLocalPath ? rec.imagePath.split('/').pop() : null),
        imagePath: isValidLocalPath ? rec.imagePath : null,
        previewUrl,
        imagePrediction: imgRes?.imagePrediction || rec.imagePrediction,
        predictedClass: imgRes?.predictedClass,
        confidence: imgRes?.confidence ?? (isValidLocalPath ? rec.confidence : null),
        isLowConfidence: imgRes?.isLowConfidence,
        isOutOfDistribution: imgRes?.isOutOfDistribution,
        hasDiseaseClassifier: imgRes?.hasDiseaseClassifier,
        uncertaintyNotice: imgRes?.uncertaintyNotice,
        classProbabilities: imgRes?.classProbabilities,
        modelValidated: imgRes ? imgRes.modelValidated : (isValidLocalPath ? false : undefined),
        trainingData: imgRes?.trainingData,
        modelStatusNote: imgRes?.modelStatusNote,
        symptoms: symRes?.selectedSymptoms || (Array.isArray(rec.symptoms) ? rec.symptoms : []),
        symptomTopCondition: symRes?.topCondition,
        symptomMatchScore: symRes?.matchScorePercent ?? (!isValidLocalPath ? rec.confidence : null),
        symptomMatchLevel: symRes?.matchLevel,
        hasRedFlag: symRes?.hasRedFlag,
        redFlags: symRes?.redFlags,
        urgencyNotice: symRes?.urgencyNotice,
        matchedConditions: symRes?.matchedConditions || [],
        symptomAnalysis: symRes?.symptomAnalysis || rec.symptomAnalysis,
        preventionTips: details.preventionTips || combDec?.preventionTips || symRes?.preventionTips || imgRes?.preventionTips,
        combinedDecision: combDec
      }
    })
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Screening History</h1>
        <p>
          Review, filter, and manage saved screening reports across all 10 supported animals. Times are shown in your local timezone.
        </p>
      </div>

      <div className="form-card">
        <div className="history-toolbar">
          <div className="history-filter-group">
            <label htmlFor="history-animal-filter">
              <strong>Filter by Animal:</strong>
            </label>
            <select
              id="history-animal-filter"
              className="form-select history-filter-select"
              value={animalFilter}
              onChange={(e) => {
                setLoading(true)
                setAnimalFilter(e.target.value)
                setStatusMsg('')
                setErrorMsg('')
              }}
            >
              <option value="all">All Animals (10)</option>
              {animals.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.emoji} {a.name}
                </option>
              ))}
            </select>
          </div>

          <div className="history-toolbar-actions">
            <button
              type="button"
              className="btn btn-outline btn-small"
              onClick={() => {
                setLoading(true)
                setErrorMsg('')
                setRefreshTick((t) => t + 1)
              }}
              disabled={loading}
            >
              Refresh
            </button>
            {records.length > 0 && (
              <button
                type="button"
                className="btn btn-outline btn-small"
                onClick={handleClearAll}
              >
                Clear All History
              </button>
            )}
          </div>
        </div>

        {statusMsg && <div className="notice-success">{statusMsg}</div>}
        {errorMsg && <div className="notice-error">{errorMsg}</div>}

        {loading ? (
          <p className="result-muted">Loading screening history...</p>
        ) : records.length === 0 ? (
          <div className="empty-history">
            <h3>No Saved Records Found</h3>
            <p>
              Run a photo upload or symptom check for any of the 10 animals to automatically save screening reports here.
            </p>
            <Link to="/select-animal" className="btn btn-primary">
              Run a Health Screening
            </Link>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Animal</th>
                  <th>Photo Status</th>
                  <th>Score</th>
                  <th>Screening Summary</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((rec) => (
                  <tr key={rec.id}>
                    <td>{formatLocalTimestamp(rec.createdAt || rec.date)}</td>
                    <td>
                      <strong>{rec.animal}</strong>
                    </td>
                    <td>{rec.imagePrediction}</td>
                    <td>
                      {rec.confidence !== null && rec.confidence !== undefined
                        ? `${rec.confidence}%`
                        : '—'}
                    </td>
                    <td>
                      <div>{rec.symptomAnalysis}</div>
                      {Array.isArray(rec.symptoms) && rec.symptoms.length > 0 && (
                        <small className="result-muted">
                          Symptoms ({rec.symptoms.length}): {rec.symptoms.join(', ')}
                        </small>
                      )}
                    </td>
                    <td>
                      <div className="history-row-actions">
                        <button
                          type="button"
                          className="btn btn-small btn-secondary"
                          onClick={() => handleViewRecord(rec)}
                        >
                          View
                        </button>
                        <button
                          type="button"
                          className="btn btn-small btn-outline"
                          onClick={() => handleDeleteRecord(rec.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default History
