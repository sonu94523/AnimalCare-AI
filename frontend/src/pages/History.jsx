import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchHistory } from '../services/api'

function History() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    fetchHistory()
      .then((data) => {
        if (mounted && Array.isArray(data)) {
          setRecords(data)
        }
      })
      .catch(() => {
        // Fallback to empty records
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Prediction History</h1>
        <p>
          View previously saved animal disease detection records from the local SQLite database.
        </p>
      </div>

      <div className="form-card">
        {loading ? (
          <p className="result-muted">Loading prediction history...</p>
        ) : records.length === 0 ? (
          <div className="empty-history">
            <h3>No Saved Records Yet</h3>
            <p>
              Detection history will be stored and retrieved from the SQLite database once backend persistence is connected (Day 5 & Day 17).
            </p>
            <Link to="/select-animal" className="btn btn-primary">
              Run a Preliminary Check
            </Link>
          </div>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Animal</th>
                <th>Image Prediction</th>
                <th>Symptom Analysis</th>
              </tr>
            </thead>
            <tbody>
              {records.map((rec) => (
                <tr key={rec.id}>
                  <td>{rec.date}</td>
                  <td>{rec.animal}</td>
                  <td>{rec.imagePrediction}</td>
                  <td>{rec.symptomAnalysis}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default History
