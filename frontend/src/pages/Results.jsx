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

          {resultData.combinedDecision && (
            <div
              className={
                resultData.combinedDecision.hasConflict || resultData.combinedDecision.isUncertain
                  ? 'notice-warning'
                  : 'notice-success'
              }
              style={{ marginBottom: '1rem' }}
            >
              <p style={{ marginBottom: '0.35rem' }}>
                <strong>Final Preliminary Assessment:</strong>{' '}
                {resultData.combinedDecision.finalConclusion}
              </p>
              <p style={{ marginBottom: '0.35rem' }}>
                <strong>Agreement / Evidence Status:</strong>{' '}
                {resultData.combinedDecision.agreementStatus} (Combined Score:{' '}
                {resultData.combinedDecision.combinedConfidence}%)
              </p>
              <p style={{ margin: 0 }}>{resultData.combinedDecision.explanation}</p>
            </div>
          )}

          <div className="result-box">
            <p>
              <strong>Image Prediction (MobileNetV2):</strong> {resultData.imagePrediction}
            </p>
            <p>
              <strong>Model Confidence:</strong>{' '}
              {resultData.confidence !== null && resultData.confidence !== undefined
                ? `${resultData.confidence}%`
                : 'N/A'}
            </p>
          </div>

          {resultData.isLowConfidence && resultData.uncertaintyNotice && (
            <div className="notice-warning" style={{ marginBottom: '1rem' }}>
              <strong>⚠️ Low Confidence / Uncertain Result:</strong> {resultData.uncertaintyNotice}
            </div>
          )}

          {Array.isArray(resultData.classProbabilities) && resultData.classProbabilities.length > 0 && (
            <div className="result-subsection" style={{ marginBottom: '1rem' }}>
              <h4>MobileNetV2 Class Probability Breakdown</h4>
              <div className="prob-list">
                {resultData.classProbabilities.map((item) => (
                  <div key={item.classId} className="prob-item">
                    <div className="prob-item-header">
                      <span>{item.label}</span>
                      <span>{item.probabilityPercent}%</span>
                    </div>
                    <div className="prob-bar-track">
                      <div
                        className="prob-bar-fill"
                        style={{ width: `${Math.min(100, Math.max(0, item.probabilityPercent))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="result-box">
            {resultData.symptomTopCondition && (
              <p>
                <strong>Rule-Based Symptom Match:</strong> {resultData.symptomTopCondition}{' '}
                {resultData.symptomMatchScore !== undefined && resultData.symptomMatchScore !== null
                  ? `(${resultData.symptomMatchScore}% — ${resultData.symptomMatchLevel || 'Rule Match'})`
                  : ''}
              </p>
            )}
            <p>
              <strong>Screening & Symptom Analysis:</strong>{' '}
              {resultData.symptomAnalysis
                ? resultData.symptomAnalysis
                : resultData.symptoms && resultData.symptoms.length > 0
                ? 'Preliminary symptom match evaluated against clinical rules'
                : 'No symptoms provided for analysis'}
            </p>
          </div>

          {Array.isArray(resultData.matchedConditions) && resultData.matchedConditions.length > 0 && (
            <div className="result-subsection" style={{ marginBottom: '1rem' }}>
              <h4>Rule-Based Condition Matches</h4>
              <div className="prob-list">
                {resultData.matchedConditions.map((cond) => (
                  <div key={cond.conditionId} className="prob-item">
                    <div className="prob-item-header">
                      <span>
                        {cond.conditionName} ({cond.matchedSymptomCount} symptom
                        {cond.matchedSymptomCount === 1 ? '' : 's'})
                      </span>
                      <span>{cond.matchScorePercent}%</span>
                    </div>
                    <div className="prob-bar-track">
                      <div
                        className="prob-bar-fill"
                        style={{ width: `${Math.min(100, Math.max(0, cond.matchScorePercent))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="result-subsection">
            <h4>Basic Preventive Guidance</h4>
            <ul className="result-list">
              {Array.isArray(resultData.preventionTips) && resultData.preventionTips.length > 0 ? (
                resultData.preventionTips.map((tip, idx) => <li key={idx}>{tip}</li>)
              ) : (
                <>
                  <li>Isolate any animal showing fever, skin nodules, or mouth lesions from the healthy herd.</li>
                  <li>Maintain clean water, dry bedding, and disinfected feeding equipment.</li>
                  <li>Control biting insects (flies, mosquitoes, ticks) around cattle sheds.</li>
                </>
              )}
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
