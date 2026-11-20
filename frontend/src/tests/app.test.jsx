import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

import Results from '../pages/Results'
import DiseaseInfo from '../pages/DiseaseInfo'
import SymptomChecker from '../pages/SymptomChecker'
import History, { formatLocalTimestamp } from '../pages/History'
import NotFound from '../pages/NotFound'
import * as api from '../services/api'

vi.mock('../services/api', () => ({
  API_BASE_URL: 'http://localhost:5000',
  checkBackendHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
  fetchAnimals: vi.fn().mockResolvedValue([]),
  fetchSymptoms: vi.fn().mockResolvedValue([]),
  fetchDiseases: vi.fn().mockResolvedValue([]),
  fetchHistory: vi.fn().mockResolvedValue([
    {
      id: 42,
      animal: 'Cow',
      animalId: 'cow',
      imagePrediction: 'No image uploaded (Symptom-only check)',
      confidence: 80,
      symptomAnalysis: 'Lumpy Skin Disease (LSD)',
      symptoms: ['Fever (High body temperature)'],
      createdAt: '2026-11-20T17:30:00Z',
      date: '2026-11-20T17:30:00Z'
    }
  ]),
  deleteHistoryRecord: vi.fn().mockResolvedValue({ deletedId: 42 }),
  clearAllHistory: vi.fn().mockResolvedValue({ deletedCount: 1 }),
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

  it('shows combined conflict explanation ahead of image uncertaintyNotice on Results', () => {
    const conflictState = {
      animal: 'Cow',
      animalId: 'cow',
      imageName: 'cow.jpg',
      imagePath: '/uploads/cow.jpg',
      previewUrl: 'http://localhost:5000/uploads/cow.jpg',
      imagePrediction: 'Uncertain / Low Confidence (Healthy)',
      confidence: 52.0,
      isLowConfidence: true,
      uncertaintyNotice: 'Model confidence is low. Please use the Symptom Checker.',
      modelValidated: false,
      symptoms: ['Blisters / vesicles on tongue, gums, muzzle, or hooves'],
      combinedDecision: {
        mode: 'combined',
        finalConclusion: 'Conflicting Findings (Healthy vs. Foot-and-Mouth Disease (FMD))',
        agreementStatus: 'Conflict / Disagreement Detected',
        combinedConfidence: 52.0,
        hasConflict: true,
        isUncertain: true,
        modelValidated: false,
        explanation: 'Disagreement detected: image output indicates Healthy whereas symptoms match FMD.'
      }
    }

    render(
      <MemoryRouter initialEntries={[{ pathname: '/results', state: conflictState }]}>
        <Routes>
          <Route path="/results" element={<Results />} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText(/Disagreement detected: image output indicates Healthy/i)).toBeInTheDocument()
    expect(screen.queryByText(/Please use the Symptom Checker/i)).not.toBeInTheDocument()
  })

  it('formats ISO UTC history timestamps into local time instead of displaying raw Z strings', async () => {
    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    )

    const expectedFormatted = formatLocalTimestamp('2026-11-20T17:30:00Z')
    await waitFor(() => {
      expect(screen.getByText(expectedFormatted)).toBeInTheDocument()
    })
    expect(screen.queryByText('2026-11-20T17:30:00Z')).not.toBeInTheDocument()
  })

  it('displays urgent veterinary red-flag alert banner on Results when hasRedFlag is true', () => {
    const urgentState = {
      animal: 'Dog',
      animalId: 'dog',
      imageName: null,
      imagePath: null,
      previewUrl: null,
      imagePrediction: 'No image uploaded (Symptom-only check)',
      confidence: null,
      symptoms: ['Bloody or foul-smelling dark diarrhea (Urgent red flag)', 'Repeated vomiting or retching'],
      symptomTopCondition: 'Canine Parvovirus / Acute Gastroenteritis Signs',
      symptomMatchScore: 87.5,
      hasRedFlag: true,
      urgencyNotice: 'Urgent clinical red flag reported (Bloody diarrhea). Contact a veterinarian immediately.',
      combinedDecision: {
        mode: 'symptom_only',
        finalConclusion: 'Symptom-Based Indication: Canine Parvovirus / Acute Gastroenteritis Signs',
        agreementStatus: 'Symptom-Only Screening (No Image Uploaded)',
        combinedConfidence: 87.5,
        explanation: 'High rule-based symptom match for Canine Parvovirus.'
      }
    }

    render(
      <MemoryRouter initialEntries={[{ pathname: '/results', state: urgentState }]}>
        <Routes>
          <Route path="/results" element={<Results />} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText(/URGENT VETERINARY ALERT/i)).toBeInTheDocument()
    expect(screen.getByText(/Rule Match/i)).toBeInTheDocument()
  })
})
