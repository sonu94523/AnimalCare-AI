import React from 'react'
import { useLocation, Link } from 'react-router-dom'

function Results() {
  const location = useLocation()
  const resultData = location.state || {
    animal: 'Cow',
    animalId: 'cow',
    imageName: null,
    previewUrl: null,
    imagePrediction: 'No active detection run yet',
    confidence: null,
    symptoms: ['Fever (High body temperature)', 'Skin lesions / sores / scabs'],
    symptomAnalysis: null
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Preliminary Screening Results</h1>
        <p>
          Review the image classification output, symptom analysis, and general preventive guidance below.
        </p>
      </div>

      <div className="results-grid">
        {/* Left column: Animal & Uploaded Image */}
        <div className="result-card">
          <h3>Animal & Input Summary</h3>
          <p className="result-item">
            <strong>Animal Category:</strong> {resultData.animal}
          </p>
          {resultData.previewUrl ? (
            <div className="image-preview-box">
              <p>
                <strong>Uploaded Image:</strong> {resultData.imageName}
              </p>
              <img src={resultData.previewUrl} alt="Uploaded animal" className="preview-img" />
            </div>
          ) : (
            <p className="result-muted">No image uploaded for this session.</p>
          )}

          <div className="result-subsection">
            <h4>Observed Symptoms Selected ({resultData.symptoms?.length || 0})</h4>
            {resultData.symptoms && resultData.symptoms.length > 0 ? (
              <ul className="result-list">
                {resultData.symptoms.map((sym, idx) => (
                  <li key={idx}>{sym}</li>
                ))}
              </ul>
            ) : (
              <p className="result-muted">No symptoms selected.</p>
            )}
          </div>
        </div>

        {/* Right column: Prediction & Guidance */}
        <div className="result-card">
          <h3>Screening Analysis</h3>
          <div className="result-box">
            <p>
              <strong>Image Prediction:</strong> {resultData.imagePrediction}
            </p>
            <p>
              <strong>Model Confidence:</strong>{' '}
              {resultData.confidence !== null && resultData.confidence !== undefined
                ? `${resultData.confidence}%`
                : 'N/A'}
            </p>
          </div>

          <div className="result-box">
            <p>
              <strong>Symptom-Based Analysis:</strong>{' '}
              {resultData.symptomAnalysis
                ? resultData.symptomAnalysis
                : resultData.symptoms && resultData.symptoms.length > 0
                ? 'Preliminary symptom match (Full rule engine connects in Week 3)'
                : 'No symptoms provided for analysis'}
            </p>
          </div>

          <div className="result-subsection">
            <h4>Basic Preventive Guidance</h4>
            <ul className="result-list">
              <li>Isolate any animal showing fever, skin nodules, or mouth lesions from the healthy herd.</li>
              <li>Maintain clean water, dry bedding, and disinfected feeding equipment.</li>
              <li>Control biting insects (flies, mosquitoes, ticks) around cattle sheds.</li>
            </ul>
          </div>

          <div className="vet-advisory-box">
            <strong>Veterinary Recommendation:</strong> This system provides preliminary academic screening only and is not a confirmed veterinary diagnosis. Do not self-medicate; consult a qualified veterinarian for examination and treatment.
          </div>
        </div>
      </div>

      <div className="form-actions" style={{ marginTop: '1.5rem' }}>
        <Link to="/select-animal" className="btn btn-primary">
          Start New Detection
        </Link>
        <Link to="/diseases" className="btn btn-secondary">
          View Disease Reference Info
        </Link>
        <Link to="/history" className="btn btn-outline">
          View Prediction History
        </Link>
      </div>
    </div>
  )
}

export default Results
