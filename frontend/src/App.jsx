import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import AnimalSelection from './pages/AnimalSelection'
import ImageDetection from './pages/ImageDetection'
import SymptomChecker from './pages/SymptomChecker'
import Results from './pages/Results'
import DiseaseInfo from './pages/DiseaseInfo'
import History from './pages/History'
import NotFound from './pages/NotFound'

function App() {
  return (
    <Router>
      <div className="app-layout">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/select-animal" element={<AnimalSelection />} />
            <Route path="/image-detection" element={<ImageDetection />} />
            <Route path="/symptoms" element={<SymptomChecker />} />
            <Route path="/results" element={<Results />} />
            <Route path="/diseases" element={<DiseaseInfo />} />
            <Route path="/history" element={<History />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  )
}

export default App
