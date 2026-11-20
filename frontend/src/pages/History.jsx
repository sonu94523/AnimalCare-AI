import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  API_BASE_URL,
  fetchHistory,
  deleteHistoryRecord,
  clearAllHistory
} from '../services/api'
import { OFFLINE_FALLBACK_ANIMALS as ANIMALS } from '../data/fallbackData'

function History() {
  const navigate = useNavigate()
  const [records, setRecords] = useState([])
  const [animalFilter, setAnimalFilter] = useState('all')
  const [refreshTick, setRefreshTick] = useState(0)
  const [adminToken, setAdminToken] = useState(import.meta.env.VITE_ADMIN_TOKEN || '')
  const [loading, setLoading] = useState(true)
  const [statusMsg, setStatusMsg] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

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
        uncertaintyNotice: imgRes?.uncertaintyNotice,
        classProbabilities: imgRes?.classProbabilities,
        modelValidated: imgRes ? imgRes.modelValidated : (isValidLocalPath ? false : undefined),
        trainingData: imgRes?.trainingData,
        modelStatusNote: imgRes?.modelStatusNote,
        symptoms: symRes?.selectedSymptoms || (Array.isArray(rec.symptoms) ? rec.symptoms : []),
        symptomTopCondition: symRes?.topCondition,
        symptomMatchScore: symRes?.matchScorePercent ?? (!isValidLocalPath ? rec.confidence : null),
        symptomMatchLevel: symRes?.matchLevel,
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
        <h1>Prediction History</h1>
        <p>
          Review, filter, and manage previously saved animal disease screening records stored in the SQLite database.
        </p>
      </div>

      <div className="form-card">
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.75rem',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1.25rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <label htmlFor="history-animal-filter" style={{ fontWeight: 600 }}>
              Filter by Animal:
            </label>
            <select
              id="history-animal-filter"
              className="form-select"
              style={{ width: 'auto', minWidth: '180px' }}
              value={animalFilter}
              onChange={(e) => {
                setLoading(true)
                setAnimalFilter(e.target.value)
                setStatusMsg('')
                setErrorMsg('')
              }}
            >
              <option value="all">All Animals</option>
              {ANIMALS.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.emoji} {a.name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
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

        {statusMsg && <div className="notice-success" style={{ marginBottom: '1rem' }}>{statusMsg}</div>}
        {errorMsg && <div className="notice-error" style={{ marginBottom: '1rem' }}>{errorMsg}</div>}

        {loading ? (
          <p className="result-muted">Loading prediction history...</p>
        ) : records.length === 0 ? (
          <div className="empty-history">
            <h3>No Saved Records Found</h3>
            <p>
              Run an image classification or symptom check to automatically store preliminary screening records in the SQLite database.
            </p>
            <Link to="/select-animal" className="btn btn-primary">
              Run a Preliminary Check
            </Link>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="history-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Animal</th>
                  <th>Image Prediction</th>
                  <th>Score / Confidence</th>
                  <th>Symptom & Screening Summary</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((rec) => (
                  <tr key={rec.id}>
                    <td>{rec.date}</td>
                    <td>
                      <strong>{rec.animal}</strong>
                    </td>
                    <td>{rec.imagePrediction}</td>
                    <td>
                      {rec.confidence !== null && rec.confidence !== undefined
                        ? `${rec.confidence}%`
                        : 'N/A'}
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
                      <div style={{ display: 'flex', gap: '0.4rem' }}>
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
