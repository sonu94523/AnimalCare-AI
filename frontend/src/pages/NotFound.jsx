import React from 'react'
import { Link } from 'react-router-dom'

function NotFound() {
  return (
    <div className="page-container">
      <div className="form-card empty-history">
        <h1>404 – Page Not Found</h1>
        <p>The page you requested does not exist in AnimalCare AI.</p>
        <div className="form-actions" style={{ justifyContent: 'center' }}>
          <Link to="/" className="btn btn-primary">
            Back to Home
          </Link>
          <Link to="/select-animal" className="btn btn-secondary">
            Start Screening
          </Link>
        </div>
      </div>
    </div>
  )
}

export default NotFound
