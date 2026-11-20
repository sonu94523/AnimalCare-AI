import React from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'

function Results() {
  const location = useLocation()
  const navigate = useNavigate()
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
            Select any of the 10 supported animals and run a symptom check or photo upload to view results here.
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

  const isPhotoOnlyWithoutClassifier =
    hasImage && !hasSymptoms && resultData.hasDiseaseClassifier === false && !resultData.isOutOfDistribution

  const showUnvalidatedBanner =
    hasImage &&
    resultData.hasDiseaseClassifier !== false &&
    (resultData.modelValidated === false || comb?.modelValidated === false)

  const isWarning = Boolean(
    resultData.hasRedFlag ||
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
      : comb?.mode === 'symptom_only' || (hasSymptoms && !hasImage) || resultData.hasDiseaseClassifier === false
      ? 'Rule Match'
      : 'Combined Score'

  const primarySubtitle =
    comb?.explanation ||
    resultData.uncertaintyNotice ||
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
        <h1>Screening Report</h1>
        <p>Preliminary health screening summary for {resultData.animal}.</p>
      </div>

      {resultData.hasRedFlag && resultData.urgencyNotice && (
        <div className="notice-urgent">
          🚨 <strong>URGENT VETERINARY ALERT:</strong> {resultData.urgencyNotice}
        </div>
      )}

      {showUnvalidatedBanner && (
        <div className="notice-warning">
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

      {isPhotoOnlyWithoutClassifier && resultData.uploadId && (
        <div className="notice-info no-print" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <span>
            <strong>Next Step:</strong> Your {resultData.animal} photo is verified and attached. Add observed clinical symptoms to run species-specific condition matching.
          </span>
          <button
            type="button"
            className="btn btn-primary btn-small"
            onClick={() =>
              navigate(`/symptoms?animal=${resultData.animalId || 'cow'}`, {
                state: {
                  uploadId: resultData.uploadId,
                  predictionResult: {
                    imagePrediction: resultData.imagePrediction,
                    predictedClass: resultData.predictedClass,
                    hasDiseaseClassifier: false
                  },
                  imagePath: resultData.imagePath,
                  previewUrl: resultData.previewUrl,
                  imageName: resultData.imageName
                }
              })
            }
          >
            Add {resultData.animal} Symptoms Now
          </button>
        </div>
      )}

      {/* Two-Column Clean Breakdown */}
      <div className="results-grid">
        <div className="result-card">
          <h3>1. Screening Evidence</h3>

          <div className="result-kpi-row">
            <div className="result-kpi-box">
              <span className="result-kpi-label">Animal</span>
              <span className="result-kpi-value">{resultData.animal}</span>
            </div>
            <div className="result-kpi-box">
              <span className="result-kpi-label">Photo Status</span>
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
            <div className="image-preview-box" style={{ width: '100%' }}>
              <span className="result-kpi-label">Uploaded Photo ({resultData.imageName})</span>
              <img src={resultData.previewUrl} alt="Uploaded animal" className="preview-img" />
            </div>
          )}

          {hasProbs && (
            <div className="result-subsection">
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
              <div className="symptom-tags">
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

        <div className="result-card">
          <h3>2. Recommended Next Steps</h3>
          <div className="action-step-list">
            {preventionList.map((tip, idx) => (
              <div key={idx} className="action-step-item">
                <span className="action-step-num">{idx + 1}</span>
                <span>{tip}</span>
              </div>
            ))}
          </div>

          <div className="vet-advisory-box">
            <strong>Veterinary Note:</strong> This tool provides preliminary academic screening only. Suspected notifiable diseases (FMD, LSD, PPR, Swine Fever, Newcastle Disease) should be reported promptly to local veterinary authorities. Always consult a qualified veterinarian before starting treatment.
          </div>
        </div>
      </div>

      <div className="form-actions no-print">
        <Link to="/select-animal" className="btn btn-primary">
          Start New Screening
        </Link>
        <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
          🖨️ Print / Save Vet Report
        </button>
        <Link to="/diseases" className="btn btn-outline">
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
