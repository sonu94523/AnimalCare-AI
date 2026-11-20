import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

import Results from '../pages/Results'
import DiseaseInfo from '../pages/DiseaseInfo'
import SymptomChecker from '../pages/SymptomChecker'
import NotFound from '../pages/NotFound'
import * as api from '../services/api'

vi.mock('../services/api', () => ({
  API_BASE_URL: 'http://localhost:5000',
  checkBackendHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
  fetchAnimals: vi.fn().mockResolvedValue([]),
  fetchSymptoms: vi.fn().mockResolvedValue([]),
  fetchDiseases: vi.fn().mockResolvedValue([]),
  fetchModelInfo: vi.fn().mockResolvedValue({
    backbone: 'MobileNetV2',
    inputShape: [224, 224, 3],
    modelLoaded: true,
    validated: false,
    trainingData: 'synthetic',
    statusNote: 'This image model has not been validated on real animals.'
  }),
  submitSymptomForm: vi.fn().mockResolvedValue({
    selectedSymptoms: ['Fever (High body temperature)', 'Firm round skin nodules (2–5 cm) on head, neck, or body'],
    topCondition: 'Lumpy Skin Disease (LSD)',
    matchScorePercent: 80.0,
    matchLevel: 'High Symptom Match',
    matchedConditions: [],
    symptomAnalysis: 'High rule-based symptom match.',
    preventionTips: ['Isolate animal.'],
    combinedDecision: {
      mode: 'symptom_only',
      finalConclusion: 'Symptom-Based Indication: Lumpy Skin Disease (LSD)',
      agreementStatus: 'Symptom-Only Screening (No Image Uploaded)',
      combinedConfidence: 80.0
    }
  }),
  submitCombinedPrediction: vi.fn()
}))

describe('AnimalCare AI Frontend Flows', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows an honest empty state on /results when visited directly without screening data', () => {
    render(
      <MemoryRouter initialEntries={['/results']}>
        <Routes>
          <Route path="/results" element={<Results />} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.getByText(/No Screening Run Yet/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Start a Screening/i })).toBeInTheDocument()
  })

  it('displays the unvalidated demo banner and accurate Image Confidence caption on image results', () => {
    const state = {
      animal: 'Cow',
      animalId: 'cow',
      imageName: 'sample.jpg',
      imagePath: '/uploads/sample.jpg',
      previewUrl: 'http://localhost:5000/uploads/sample.jpg',
      imagePrediction: 'Lumpy Skin Disease (LSD) (Demo Model — Not Validated)',
      confidence: 82.5,
      modelValidated: false,
      symptoms: [],
      combinedDecision: {
        mode: 'image_only',
        finalConclusion: 'Demo Image Output: Lumpy Skin Disease (LSD)',
        agreementStatus: 'Demo Model Output — Not Clinically Validated',
        combinedConfidence: 82.5,
        modelValidated: false,
        explanation: 'Demo output only.'
      }
    }

    render(
      <MemoryRouter initialEntries={[{ pathname: '/results', state }]}>
        <Routes>
          <Route path="/results" element={<Results />} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText(/Unvalidated Demo Model — Non-Diagnostic/i)).toBeInTheDocument()
    expect(screen.getByText('Image Confidence')).toBeInTheDocument()
    expect(screen.getByText('82.5%')).toBeInTheDocument()
  })

  it('shows Not Validated status on DiseaseInfo and never displays a misleading 100% accuracy banner', async () => {
    render(
      <MemoryRouter>
        <DiseaseInfo />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Not Validated on Real Animals \(Demo Only\)/i)).toBeInTheDocument()
    })
    expect(screen.queryByText(/Test Set Accuracy/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/100%/i)).not.toBeInTheDocument()
  })

  it('submits canonical symptom IDs rather than display labels from SymptomChecker', async () => {
    render(
      <MemoryRouter initialEntries={['/symptoms?animal=cow']}>
        <Routes>
          <Route path="/symptoms" element={<SymptomChecker />} />
          <Route path="/results" element={<Results />} />
        </Routes>
      </MemoryRouter>
    )

    fireEvent.click(screen.getByLabelText(/Fever \(High body temperature\)/i))
    fireEvent.click(screen.getByLabelText(/Firm round skin nodules/i))
    fireEvent.click(screen.getByRole('button', { name: /Submit & Analyze Symptoms/i }))

    await waitFor(() => {
      expect(api.submitSymptomForm).toHaveBeenCalledWith('cow', ['fever', 'skin_nodules'])
    })
  })

  it('renders 404 NotFound page for unknown routes', () => {
    render(
      <MemoryRouter initialEntries={['/does-not-exist']}>
        <Routes>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.getByText(/404 – Page Not Found/i)).toBeInTheDocument()
  })
})
