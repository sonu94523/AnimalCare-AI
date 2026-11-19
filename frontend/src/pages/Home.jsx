import React from 'react'
import { Link } from 'react-router-dom'

const ANIMAL_CATEGORIES = [
  {
    id: 'cow',
    name: 'Cow',
    emoji: '🐄',
    aiSupported: true,
    statusText: 'AI Image + Symptom Detection Available',
    description: 'Supports MobileNetV2 image screening (Healthy, Lumpy Skin Disease, Foot-and-Mouth Disease) and symptom analysis.'
  },
  {
    id: 'buffalo',
    name: 'Buffalo',
    emoji: '🐃',
    aiSupported: true,
    statusText: 'AI Image + Symptom Detection Available',
    description: 'Supports MobileNetV2 image screening and rule-based symptom screening for common bovine conditions.'
  },
  {
    id: 'goat',
    name: 'Goat',
    emoji: '🐐',
    aiSupported: false,
    statusText: 'AI Image Detection Unavailable',
    description: 'Displayed in interface. AI image model pending verified dataset; basic symptom reference only.'
  },
  {
    id: 'sheep',
    name: 'Sheep',
    emoji: '🐑',
    aiSupported: false,
    statusText: 'AI Image Detection Unavailable',
    description: 'Displayed in interface. AI image model pending verified dataset; basic symptom reference only.'
  },
  {
    id: 'dog',
    name: 'Dog',
    emoji: '🐕',
    aiSupported: false,
    statusText: 'AI Image Detection Unavailable',
    description: 'Displayed in interface. AI image model pending verified dataset; basic symptom reference only.'
  },
  {
    id: 'cat',
    name: 'Cat',
    emoji: '🐈',
    aiSupported: false,
    statusText: 'AI Image Detection Unavailable',
    description: 'Displayed in interface. AI image model pending verified dataset; basic symptom reference only.'
  }
]

const HOW_IT_WORKS_STEPS = [
  {
    step: '1',
    title: 'Select an Animal',
    description: 'Choose from 6 animal categories. Full AI image detection is currently active for Cow and Buffalo.'
  },
  {
    step: '2',
    title: 'Upload Animal Image',
    description: 'Upload a clear JPG, JPEG, or PNG photo of the affected area for MobileNetV2 image classification.'
  },
  {
    step: '3',
    title: 'Select Observed Symptoms',
    description: 'Check visible symptoms such as fever, skin lesions, swelling, loss of appetite, or reduced milk yield.'
  },
  {
    step: '4',
    title: 'View Preliminary Results',
    description: 'Review combined image prediction, symptom matches, preventive care tips, and veterinary guidance.'
  }
]

function Home() {
  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <span className="hero-badge">Academic AI & Veterinary Screening Project</span>
          <h1>AnimalCare AI – Animal Disease Detection System</h1>
          <p className="hero-description">
            A simple, accessible web application that helps farmers, pet owners, and students perform preliminary animal disease screening using MobileNetV2 image classification and rule-based symptom analysis.
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

      {/* About Disease Detection Info Section */}
      <section className="section">
        <div className="section-header">
          <h2>Animal Disease Detection Information</h2>
          <p>
            Early identification of livestock and companion animal diseases helps prevent severe outbreaks and supports timely veterinary care.
          </p>
        </div>
        <div className="info-grid">
          <div className="info-card">
            <h3>📷 Image-Based Screening</h3>
            <p>
              Uses transfer learning with <strong>MobileNetV2</strong> (224 × 224 RGB preprocessing) to classify uploaded photos of cows and buffaloes into supported conditions such as Healthy, Lumpy Skin Disease, and Foot-and-Mouth Disease.
            </p>
          </div>
          <div className="info-card">
            <h3>🩺 Symptom-Based Analysis</h3>
            <p>
              Matches observed clinical signs—such as fever, skin nodules, mouth blisters, lameness, and loss of appetite—against verified veterinary symptom rules to highlight possible conditions.
            </p>
          </div>
          <div className="info-card">
            <h3>⚠️ Honest Uncertainty Handling</h3>
            <p>
              When image predictions have low confidence or disagree with selected symptoms, the system clearly reports uncertainty rather than guessing or prescribing medications.
            </p>
          </div>
        </div>
      </section>

      {/* Supported Animal Categories */}
      <section className="section">
        <div className="section-header">
          <h2>Supported Animal Categories</h2>
          <p>
            Actual AI image detection is implemented for <strong>Cow</strong> and <strong>Buffalo</strong>. Other categories are shown with their current availability status.
          </p>
        </div>
        <div className="animal-grid">
          {ANIMAL_CATEGORIES.map((animal) => (
            <div
              key={animal.id}
              className={`animal-card ${animal.aiSupported ? 'animal-supported' : 'animal-unsupported'}`}
            >
              <div className="animal-card-top">
                <span className="animal-emoji" role="img" aria-label={animal.name}>
                  {animal.emoji}
                </span>
                <span className={`status-pill ${animal.aiSupported ? 'pill-active' : 'pill-inactive'}`}>
                  {animal.statusText}
                </span>
              </div>
              <h3>{animal.name}</h3>
              <p>{animal.description}</p>
              <div className="animal-card-Action">
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

      {/* How the Application Works */}
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
