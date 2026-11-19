import React, { useEffect, useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
import { checkBackendHealth } from '../services/api'

function Navbar() {
  const [apiOnline, setApiOnline] = useState(null)

  useEffect(() => {
    let mounted = true
    checkBackendHealth()
      .then((data) => {
        if (mounted && data?.status === 'ok') {
          setApiOnline(true)
        }
      })
      .catch(() => {
        if (mounted) {
          setApiOnline(false)
        }
      })
    return () => {
      mounted = false
    }
  }, [])

  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-left">
          <Link to="/" className="navbar-brand">
            <span className="brand-icon">🐾</span>
            <span>AnimalCare AI</span>
          </Link>
          {apiOnline !== null && (
            <span
              className={`api-status-dot ${apiOnline ? 'api-online' : 'api-offline'}`}
              title={apiOnline ? 'Flask Backend Connected' : 'Flask Backend Offline (Using Fallback Data)'}
            >
              {apiOnline ? '● API Connected' : '○ API Offline'}
            </span>
          )}
        </div>
        <nav className="navbar-links">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Home
          </NavLink>
          <NavLink to="/select-animal" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Select Animal
          </NavLink>
          <NavLink to="/image-detection" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Image Detection
          </NavLink>
          <NavLink to="/symptoms" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Symptom Checker
          </NavLink>
          <NavLink to="/diseases" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Disease Info
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            History
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

export default Navbar
