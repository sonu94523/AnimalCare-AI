import React from 'react'

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <p className="footer-title">
          <strong>AnimalCare AI</strong> – Simple Animal Disease Detection System
        </p>
        <p className="footer-disclaimer">
          Disclaimer: This college project provides preliminary disease screening only and does not replace professional veterinary diagnosis. Always consult a qualified veterinarian.
        </p>
        <p className="footer-copy">© {new Date().getFullYear()} AnimalCare AI Academic Project</p>
      </div>
    </footer>
  )
}

export default Footer
