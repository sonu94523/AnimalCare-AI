import React from 'react'
import { useLocation, Link } from 'react-router-dom'

function Results() {
  const location = useLocation()
  const resultData = location.state

  if (!resultData) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h1>Screening Result</h1>
          <p>No active screening session found.</p>
        </div>
        <div className="form-card empty-history">
          <h3>No Screening Run Yet</h3>
          <p>
            Select an animal category and run a symptom check or demo image upload to view results here.
          </p>
          <div className="form-actions" style={{ justifyContent: 'center' }}>
            <Link to="/select-animal" className="btn btn-primary">
              Start a Screening
            </Link>
            <Link to="/history" className="btn btn-outline">
              View Saved History
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const comb = resultData.combinedDecision
  const hasSymptoms = Array.isArray(resultData.symptoms) && resultData.symptoms.length > 0
  const hasImage = Boolean(resultData.previewUrl || resultData.imagePath)
  const hasProbs = Array.isArray(resultData.classProbabilities) && resultData.classProbabilities.length > 0
  const hasMatchedConds =
    Array.isArray(resultData.matchedConditions) && resultData.matchedConditions.length > 0

  const showUnvalidatedBanner =
    hasImage && (resultData.modelValidated === false || comb?.modelValidated === false)

  const isWarning = Boolean(
    comb?.hasConflict ||
      comb?.isUncertain ||
      resultData.isLowConfidence ||
      resultData.isOutOfDistribution ||
      showUnvalidatedBanner
  )

  const primaryHeadline =
    comb?.finalConclusion ||
    resultData.symptomTopCondition ||
    resultData.imagePrediction ||
    'Preliminary Screening Complete'

  const primaryScore =
    comb?.combinedConfidence ??
    resultData.confidence ??
    resultData.symptomMatchScore ??
    null

  const scoreCaption =
    comb?.mode === 'image_only' || (hasImage && !hasSymptoms)
      ? 'Image Confidence'
      : comb?.mode === 'symptom_only' || (hasSymptoms && !hasImage)
      ? 'Rule Match'
      : 'Combined Score'

  const primarySubtitle =
    resultData.uncertaintyNotice ||
    comb?.explanation ||
    resultData.symptomAnalysis ||
    'Review the detection metrics and preventive care steps below.'

  const preventionList =
    Array.isArray(resultData.preventionTips) && resultData.preventionTips.length > 0
      ? resultData.preventionTips
      : [
          'Isolate any animal showing fever, skin nodules, or mouth lesions from the healthy herd.',
          'Maintain clean water, dry bedding, and disinfected feeding equipment.',
          'Consult a qualified veterinarian and report suspected notifiable diseases to local authorities.'
        ]

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Screening Result</h1>
        <p>Clear summary of your screening check.</p>
      </div>

      {showUnvalidatedBanner && (
        <div className="notice-warning" style={{ marginBottom: '1rem' }}>
          <strong>Unvalidated Demo Model — Non-Diagnostic:</strong>{' '}
          {resultData.modelStatusNote ||
            'This image model has not been validated on real animals (trained on synthetic placeholder data). Do not treat the image output as a medical diagnosis.'}
        </div>
      )}

      {/* Top Hero Summary Card */}
      <div className={`result-hero-card ${isWarning ? 'result-hero-warn' : ''}`}>
        <div className="result-hero-main">
          <div className="result-hero-label">
            {comb?.agreementStatus || (isWarning ? '⚠️ Preliminary Notice' : '✓ Screening Result')}
          </div>
          <div className="result-hero-title">{primaryHeadline}</div>
          <p className="result-hero-subtitle">{primarySubtitle}</p>
        </div>

        {primaryScore !== null && primaryScore !== undefined && (
          <div className="result-score-badge">
            <span className="result-score-number">{primaryScore}%</span>
            <span className="result-score-caption">{scoreCaption}</span>
          </div>
        )}
      </div>

      {/* Two-Column Clean Breakdown */}
      <div className="results-grid">
        {/* Left Card: Detection Evidence */}
        <div className="result-card">
          <h3>1. Detection Breakdown</h3>

          <div className="result-kpi-row">
            <div className="result-kpi-box">
              <span className="result-kpi-label">Animal</span>
              <span className="result-kpi-value">{resultData.animal}</span>
            </div>
            <div className="result-kpi-box">
              <span className="result-kpi-label">Image Check</span>
              <span className="result-kpi-value">
                {hasImage ? resultData.imagePrediction : 'Not Uploaded'}
              </span>
            </div>
            <div className="result-kpi-box">
              <span className="result-kpi-label">Symptoms Checked</span>
              <span className="result-kpi-value">
                {hasSymptoms ? `${resultData.symptoms.length} Selected` : 'None'}
              </span>
            </div>
          </div>

          {resultData.previewUrl && (
            <div className="image-preview-box" style={{ width: '100%', marginBottom: '1rem' }}>
              <span className="result-kpi-label">Uploaded Photo ({resultData.imageName})</span>
              <img src={resultData.previewUrl} alt="Uploaded animal" className="preview-img" />
            </div>
          )}

          {hasProbs && (
            <div className="result-subsection" style={{ marginTop: '0.5rem' }}>
              <h4>Demo Image Model Probabilities (Non-Diagnostic)</h4>
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

          {hasSymptoms && (
            <div className="result-subsection">
              <h4>Observed Symptoms</h4>
              <div className="symptom-tags" style={{ marginTop: '0.4rem' }}>
                {resultData.symptoms.map((sym, idx) => (
                  <span key={idx} className="symptom-tag">
                    {sym}
                  </span>
                ))}
              </div>
            </div>
          )}

          {hasMatchedConds && (
            <div className="result-subsection">
              <h4>Symptom Rule Matches</h4>
              <div className="prob-list">
                {resultData.matchedConditions.map((cond) => (
                  <div key={cond.conditionId} className="prob-item">
                    <div className="prob-item-header">
                      <span>{cond.conditionName}</span>
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
        </div>

        {/* Right Card: Recommended Action Steps */}
        <div className="result-card">
          <h3>2. Recommended Next Steps</h3>
          <div className="steps-grid" style={{ gridTemplateColumns: '1fr', gap: '0.75rem', marginBottom: '1rem' }}>
            {preventionList.map((tip, idx) => (
              <div
                key={idx}
                className="result-box"
                style={{
                  margin: 0,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.75rem'
                }}
              >
                <span
                  className="step-number"
                  style={{
                    margin: 0,
                    width: '28px',
                    height: '28px',
                    fontSize: '0.85rem',
                    flexShrink: 0
                  }}
                >
                  {idx + 1}
                </span>
                <span style={{ fontSize: '0.94rem', color: '#1f2937' }}>{tip}</span>
              </div>
            ))}
          </div>

          <div className="vet-advisory-box">
            <strong>Veterinary Note:</strong> This tool provides preliminary academic screening only. Suspected FMD or LSD should be reported promptly to local veterinary authorities. Always consult a qualified veterinarian before starting treatment.
          </div>
        </div>
      </div>

      <div className="form-actions" style={{ marginTop: '1.5rem' }}>
        <Link to="/select-animal" className="btn btn-primary">
          Start New Detection
        </Link>
        <Link to="/diseases" className="btn btn-secondary">
          Disease Reference Guide
        </Link>
        <Link to="/history" className="btn btn-outline">
          Prediction History
        </Link>
      </div>
    </div>
  )
}

export default Results
