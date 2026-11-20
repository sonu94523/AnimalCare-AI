import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { OFFLINE_FALLBACK_ANIMALS } from '../data/fallbackData'
import { fetchAnimals } from '../services/api'

const HOW_IT_WORKS_STEPS = [
  {
    step: '1',
    title: 'Select an Animal',
    description: 'Choose from 6 animal categories. Demo image screening is configured for Cow and Buffalo.'
  },
  {
    step: '2',
    title: 'Upload Animal Image (Demo)',
    description: 'Upload a JPG, JPEG, or PNG photo to exercise the 224 × 224 MobileNetV2 pipeline (not clinically validated).'
  },
  {
    step: '3',
    title: 'Select Observed Symptoms',
    description: 'Check visible clinical signs such as fever, skin nodules, mouth blisters, lameness, or reduced milk yield.'
  },
  {
    step: '4',
    title: 'View Preliminary Results',
    description: 'Review symptom matches, demo image output, agreement/conflict flags, and veterinary guidance.'
  }
]

function Home() {
  const [animals, setAnimals] = useState(OFFLINE_FALLBACK_ANIMALS)

  useEffect(() => {
    let mounted = true
    fetchAnimals()
      .then((data) => {
        if (mounted && Array.isArray(data) && data.length > 0) {
          setAnimals(data)
        }
      })
      .catch(() => {
        // Keep OFFLINE_FALLBACK_ANIMALS when backend is unreachable
      })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div className="home-page">
      <section className="hero-section">
        <div className="hero-content">
          <span className="hero-badge">Academic AI & Veterinary Screening Project</span>
          <h1>AnimalCare AI – Animal Disease Detection System</h1>
          <p className="hero-description">
            A simple, accessible web application for preliminary animal disease screening combining a rule-based clinical symptom checker with a MobileNetV2 image classification demo pipeline.
          </p>
          <div className="hero-actions">
            <Link to="/select-animal" className="btn btn-primary">
              Start Detection
            </Link>
            <Link to="/diseases" className="btn btn-secondary">
              View Supported Diseases
            </Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h2>Animal Disease Detection Information</h2>
          <p>
            Early identification of livestock and companion animal diseases helps prevent severe outbreaks and supports timely veterinary care.
          </p>
        </div>
        <div className="info-grid">
          <div className="info-card">
            <h3>📷 Image-Based Screening (Demo)</h3>
            <p>
              Demonstrates transfer learning with <strong>MobileNetV2</strong> (224 × 224 RGB preprocessing) for Cow and Buffalo photos. Not clinically validated until retrained on real labelled photographs.
            </p>
          </div>
          <div className="info-card">
            <h3>🩺 Symptom-Based Analysis</h3>
            <p>
              Matches observed clinical signs—such as fever, skin nodules, mouth blisters, lameness, and loss of appetite—against weighted veterinary symptom rules to highlight possible conditions.
            </p>
          </div>
          <div className="info-card">
            <h3>⚠️ Honest Uncertainty Handling</h3>
            <p>
              Rejects blank/unsuitable images, flags low-confidence outputs or image-vs-symptom conflicts, and never prescribes medication dosages.
            </p>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h2>Supported Animal Categories</h2>
          <p>
            Demo image screening is configured for <strong>Cow</strong> and <strong>Buffalo</strong>. Other categories use symptom screening only.
          </p>
        </div>
        <div className="animal-grid">
          {animals.map((animal) => (
            <div
              key={animal.id}
              className={`animal-card ${animal.aiSupported ? 'animal-supported' : 'animal-unsupported'}`}
            >
              <div className="animal-card-top">
                <span className="animal-emoji" role="img" aria-label={animal.name}>
                  {animal.emoji}
                </span>
                <span className={`status-pill ${animal.aiSupported ? 'pill-active' : 'pill-inactive'}`}>
                  {animal.badge}
                </span>
              </div>
              <h3>{animal.name}</h3>
              <p>{animal.details}</p>
              <div className="animal-card-action">
                <Link
                  to={`/select-animal?animal=${animal.id}`}
                  className={`btn btn-small ${animal.aiSupported ? 'btn-primary' : 'btn-outline'}`}
                >
                  {animal.aiSupported ? `Select ${animal.name}` : 'View Category Status'}
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="section how-it-works-section">
        <div className="section-header">
          <h2>How the Application Works</h2>
          <p>Follow four simple steps to run a preliminary disease check.</p>
        </div>
        <div className="steps-grid">
          {HOW_IT_WORKS_STEPS.map((item) => (
            <div key={item.step} className="step-card">
              <div className="step-number">{item.step}</div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </div>
          ))}
        </div>
        <div className="cta-center">
          <Link to="/select-animal" className="btn btn-primary">
            Start Detection Now
          </Link>
        </div>
      </section>
    </div>
  )
}

export default Home
