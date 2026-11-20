import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { OFFLINE_FALLBACK_ANIMALS } from '../data/fallbackData'
import { fetchAnimals } from '../services/api'

const CATEGORY_TABS = [
  { id: 'all', label: 'All Animals' },
  { id: 'livestock', label: 'Livestock' },
  { id: 'poultry', label: 'Poultry' },
  { id: 'pet', label: 'Companion Pets' }
]

const HOW_IT_WORKS_STEPS = [
  {
    step: '1',
    title: 'Choose Any of 10 Animals',
    description: 'Select from Livestock (Cow, Buffalo, Goat, Sheep, Horse, Pig), Poultry (Chicken), or Pets (Dog, Cat, Rabbit).'
  },
  {
    step: '2',
    title: 'Attach a Photo (Optional)',
    description: 'Upload a photo to verify image quality and run the MobileNetV2 demo classifier (Cow/Buffalo) or attach it to your vet report.'
  },
  {
    step: '3',
    title: 'Check Clinical Symptoms',
    description: 'Select observed general and species-specific clinical signs—including urgent red-flag indicators.'
  },
  {
    step: '4',
    title: 'Get Your Screening Report',
    description: 'View ranked condition matches, prevention steps, printable vet summary, and saved local history.'
  }
]

function Home() {
  const [animals, setAnimals] = useState(OFFLINE_FALLBACK_ANIMALS)
  const [categoryFilter, setCategoryFilter] = useState('all')

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

  const visibleAnimals =
    categoryFilter === 'all'
      ? animals
      : animals.filter((a) => (a.category || 'livestock') === categoryFilter)

  return (
    <div className="home-page">
      <section className="hero-section">
        <div className="hero-content">
          <span className="hero-badge">Multi-Species Veterinary Screening Platform</span>
          <h1>AnimalCare AI – Preliminary Health Screening for 10 Animal Species</h1>
          <p className="hero-description">
            Screen livestock, poultry, and companion pets in minutes using species-specific clinical symptom rules, photo quality verification, and a MobileNetV2 image classification demo pipeline.
          </p>
          <div className="hero-actions">
            <Link to="/select-animal" className="btn btn-primary">
              Start Health Screening
            </Link>
            <Link to="/diseases" className="btn btn-secondary">
              Browse 11 Disease Guides
            </Link>
          </div>
          <div className="hero-stats">
            <div className="hero-stat-item">
              <span className="hero-stat-num">10 Species</span>
              <span className="hero-stat-label">Livestock, Poultry & Pets</span>
            </div>
            <div className="hero-stat-item">
              <span className="hero-stat-num">25 Signs</span>
              <span className="hero-stat-label">Tailored Clinical Symptoms</span>
            </div>
            <div className="hero-stat-item">
              <span className="hero-stat-num">Photo + Rules</span>
              <span className="hero-stat-label">Combined Vet Reports</span>
            </div>
            <div className="hero-stat-item">
              <span className="hero-stat-num">Honest AI</span>
              <span className="hero-stat-label">Clear Uncertainty Alerts</span>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h2>How AnimalCare AI Helps</h2>
          <p>
            Designed for clear, honest preliminary screening across farm animals and household pets without faking diagnoses.
          </p>
        </div>
        <div className="info-grid">
          <div className="info-card">
            <h3>🩺 Species-Specific Symptom Rules</h3>
            <p>
              Weighted clinical rules covering LSD, FMD, Mastitis, PPR, Equine Colic, Swine Fever, Newcastle Disease, Canine Parvo, Feline URI, and Rabbit GI Stasis—with urgent red-flag alerts.
            </p>
          </div>
          <div className="info-card">
            <h3>📷 Photo Screening & Attachment</h3>
            <p>
              Upload photos for <strong>all 10 animals</strong> (EXIF-stripped and quality-checked). Runs the MobileNetV2 demo classifier for Cow & Buffalo and attaches verified photos for every species.
            </p>
          </div>
          <div className="info-card">
            <h3>⚠️ Transparent Limitations</h3>
            <p>
              Explicitly flags unvalidated demo image outputs, rejects blank frames, highlights image-vs-symptom conflicts, and includes printable summaries for veterinary visits.
            </p>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h2>All 10 Supported Animals</h2>
          <p>
            Every animal below supports photo upload, species-specific symptom screening, combined reports, and saved history.
          </p>
        </div>

        <div className="filter-bar" style={{ justifyContent: 'center' }}>
          <div className="category-tabs">
            {CATEGORY_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`category-tab ${categoryFilter === tab.id ? 'active' : ''}`}
                onClick={() => setCategoryFilter(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="animal-grid">
          {visibleAnimals.map((animal) => (
            <div
              key={animal.id}
              className={`animal-card ${animal.aiSupported ? 'animal-supported' : 'animal-unsupported'}`}
            >
              <div>
                <div className="animal-card-top">
                  <span className="animal-emoji" role="img" aria-label={animal.name}>
                    {animal.emoji}
                  </span>
                  <span className={`status-pill ${animal.aiSupported ? 'pill-active' : 'pill-info'}`}>
                    {animal.badge}
                  </span>
                </div>
                <span className="animal-category-tag">{animal.category || 'livestock'}</span>
                <h3>{animal.name}</h3>
                <p>{animal.details}</p>
              </div>
              <div className="animal-card-action">
                <Link
                  to={`/select-animal?animal=${animal.id}`}
                  className="btn btn-small btn-primary btn-block"
                >
                  Screen {animal.name}
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="section how-it-works-section">
        <div className="section-header">
          <h2>How the Application Works</h2>
          <p>Four quick steps to generate a clear preliminary report for any supported animal.</p>
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
            Start Screening Now
          </Link>
        </div>
      </section>
    </div>
  )
}

export default Home
