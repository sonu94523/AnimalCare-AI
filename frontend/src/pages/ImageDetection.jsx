import React, { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { ANIMALS } from './AnimalSelection'
import { uploadAnimalImage, predictAnimalImage } from '../services/api'

const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png']
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 // 5 MB

function ImageDetection() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const paramAnimal = searchParams.get('animal') || 'cow'
  const [animalId, setAnimalId] = useState(paramAnimal)
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [uploading, setUploading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  useEffect(() => {
    if (ANIMALS.some((a) => a.id === paramAnimal)) {
      setAnimalId(paramAnimal)
    }
  }, [paramAnimal])

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const currentAnimal = ANIMALS.find((a) => a.id === animalId) || ANIMALS[0]

  const updatePreview = (file) => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(file ? URL.createObjectURL(file) : '')
  }

  const validateFile = (file) => {
    const ext = file.name.includes('.') ? file.name.split('.').pop().toLowerCase() : ''
    if (!ALLOWED_MIME_TYPES.includes(file.type) || !ALLOWED_EXTENSIONS.includes(ext)) {
      return 'Invalid image format. Please select a JPG, JPEG, or PNG image.'
    }
    if (file.size === 0) {
      return 'The selected image file is empty.'
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds the 5 MB limit.`
    }
    return null
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    setErrorMsg('')
    setSuccessMsg('')

    if (!file) {
      setSelectedFile(null)
      updatePreview(null)
      return
    }

    const validationError = validateFile(file)
    if (validationError) {
      setErrorMsg(validationError)
      setSelectedFile(null)
      updatePreview(null)
      e.target.value = ''
      return
    }

    setSelectedFile(file)
    updatePreview(file)
  }

  const handleLoadSyntheticDemoImage = (sampleType) => {
    setErrorMsg('')
    setSuccessMsg('')

    const canvas = document.createElement('canvas')
    canvas.width = 224
    canvas.height = 224
    const ctx = canvas.getContext('2d')

    // Synthetic coloured-noise placeholder patterns used only to test the pipeline.
    if (sampleType === 'healthy') {
      ctx.fillStyle = 'rgb(90, 155, 85)'
      ctx.fillRect(0, 0, 224, 224)
      ctx.fillStyle = 'rgb(102, 168, 96)'
      for (let i = 0; i < 40; i += 1) {
        ctx.fillRect((i * 37) % 210, (i * 53) % 210, 10, 10)
      }
    } else if (sampleType === 'lsd') {
      ctx.fillStyle = 'rgb(165, 110, 80)'
      ctx.fillRect(0, 0, 224, 224)
      ctx.fillStyle = 'rgb(107, 71, 52)'
      const spots = [
        [45, 55, 11],
        [95, 70, 12],
        [150, 60, 10],
        [70, 130, 13],
        [135, 140, 12],
        [175, 120, 9],
        [60, 180, 10],
        [120, 185, 11]
      ]
      spots.forEach(([x, y, r]) => {
        ctx.beginPath()
        ctx.arc(x, y, r, 0, Math.PI * 2)
        ctx.fill()
      })
    } else {
      ctx.fillStyle = 'rgb(180, 95, 95)'
      ctx.fillRect(0, 0, 224, 224)
      ctx.fillStyle = 'rgb(235, 110, 110)'
      const patches = [
        [30, 40, 35, 16],
        [90, 75, 38, 18],
        [140, 50, 32, 15],
        [55, 135, 36, 18],
        [125, 155, 34, 16]
      ]
      patches.forEach(([x, y, w, h]) => {
        ctx.fillRect(x, y, w, h)
      })
    }

    canvas.toBlob((blob) => {
      if (!blob) return
      const fname = `synthetic_${currentAnimal.id}_${sampleType}.png`
      const demoFile = new File([blob], fname, { type: 'image/png' })
      setSelectedFile(demoFile)
      updatePreview(demoFile)
      setSuccessMsg(
        `Loaded synthetic placeholder image (${fname}). This is NOT a real animal photo — use it only to test the upload and inference flow.`
      )
    }, 'image/png')
  }

  const handleProceedToResults = async (e) => {
    e.preventDefault()
    if (!currentAnimal.aiSupported) {
      setErrorMsg(`AI image detection is not available for ${currentAnimal.name}.`)
      return
    }
    if (!selectedFile) {
      setErrorMsg('Please select an animal image before running detection.')
      return
    }

    setUploading(true)
    setErrorMsg('')
    try {
      const data = await predictAnimalImage(selectedFile, currentAnimal.id)
      const uploadData = data.upload
      const pred = data.prediction

      navigate('/results', {
        state: {
          animal: currentAnimal.name,
          animalId: currentAnimal.id,
          imageName: uploadData.originalName || selectedFile.name,
          imagePath: uploadData.imagePath,
          previewUrl: `${import.meta.env.VITE_API_URL || 'http://localhost:5000'}${uploadData.imagePath}`,
          imagePrediction: pred.imagePrediction,
          predictedClass: pred.predictedClass,
          confidence: pred.confidence,
          isLowConfidence: pred.isLowConfidence,
          isOutOfDistribution: pred.isOutOfDistribution,
          uncertaintyNotice: pred.uncertaintyNotice,
          classProbabilities: pred.classProbabilities,
          modelValidated: pred.modelValidated,
          trainingData: pred.trainingData,
          modelStatusNote: pred.modelStatusNote,
          symptomAnalysis: pred.summary,
          preventionTips: pred.preventionTips,
          combinedDecision: data.combinedDecision,
          symptoms: []
        }
      })
    } catch (err) {
      const serverError = err?.response?.data?.error
      setErrorMsg(
        serverError ||
          'Could not run MobileNetV2 image prediction. Ensure the Flask backend is running on port 5000 and model weights are trained.'
      )
    } finally {
      setUploading(false)
    }
  }

  const handleProceedToCombinedSymptoms = async () => {
    if (!selectedFile) {
      navigate(`/symptoms?animal=${currentAnimal.id}`)
      return
    }

    setUploading(true)
    setErrorMsg('')
    try {
      const data = await uploadAnimalImage(selectedFile, currentAnimal.id)
      const uploadData = data.upload
      navigate(`/symptoms?animal=${currentAnimal.id}`, {
        state: {
          uploadId: data.uploadId || uploadData.uploadId,
          predictionResult: data.prediction,
          imagePath: uploadData.imagePath,
          previewUrl: `${import.meta.env.VITE_API_URL || 'http://localhost:5000'}${uploadData.imagePath}`,
          imageName: uploadData.originalName || selectedFile.name
        }
      })
    } catch (err) {
      const serverError = err?.response?.data?.error
      setErrorMsg(
        serverError ||
          'Could not upload image for combined screening. Ensure the Flask backend is running and model weights are trained.'
      )
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Image-Based Screening (Demo Model)</h1>
        <p>
          Upload a clear photograph (JPG, JPEG, or PNG, max 5 MB). Images are re-encoded to strip metadata and resized to 224 × 224 RGB.
        </p>
      </div>

      <div className="notice-warning" style={{ marginBottom: '1.25rem' }}>
        <strong>Demo Model — Not Validated on Real Animals:</strong> Unless retrained on real labelled cattle photos, the image classifier is trained only on synthetic placeholder patterns. Image results are for pipeline demonstration only and must not be used for diagnosis. Use the Symptom Checker and consult a veterinarian.
      </div>

      <div className="form-card">
        <div className="form-group">
          <label htmlFor="animal-select">Animal Category</label>
          <select
            id="animal-select"
            className="form-select"
            value={animalId}
            onChange={(e) => {
              setAnimalId(e.target.value)
              setErrorMsg('')
              setSuccessMsg('')
            }}
          >
            {ANIMALS.map((a) => (
              <option key={a.id} value={a.id}>
                {a.emoji} {a.name} ({a.aiSupported ? 'Demo Image + Symptoms' : 'AI Unavailable'})
              </option>
            ))}
          </select>
        </div>

        {!currentAnimal.aiSupported ? (
          <div className="notice-warning">
            <p>
              <strong>AI Image Detection Unavailable for {currentAnimal.name}:</strong> Image classification is only configured for <strong>Cow</strong> and <strong>Buffalo</strong>.
            </p>
            <div style={{ marginTop: '1rem' }}>
              <Link to={`/symptoms?animal=${currentAnimal.id}`} className="btn btn-secondary">
                Use Symptom Checker Instead
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleProceedToResults}>
            <div className="sample-demo-box">
              <p>
                <strong>Synthetic Placeholder Samples (Pipeline Test Only — Not Real Animal Photos):</strong>
              </p>
              <div className="sample-demo-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                  onClick={() => handleLoadSyntheticDemoImage('healthy')}
                >
                  Synthetic Healthy Pattern
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                  onClick={() => handleLoadSyntheticDemoImage('lsd')}
                >
                  Synthetic LSD Pattern
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
                  onClick={() => handleLoadSyntheticDemoImage('fmd')}
                >
                  Synthetic FMD Pattern
                </button>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="image-upload">
                Upload Animal Photograph (Allowed: JPG, JPEG, PNG | Max size: 5 MB)
              </label>
              <input
                id="image-upload"
                type="file"
                accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                onChange={handleFileChange}
                className="form-input-file"
              />
            </div>

            {errorMsg && <div className="notice-error">{errorMsg}</div>}
            {successMsg && <div className="notice-success">{successMsg}</div>}

            {previewUrl && selectedFile && (
              <div className="image-preview-box">
                <p>
                  <strong>Image Preview:</strong> {selectedFile.name} (
                  {(selectedFile.size / 1024).toFixed(1)} KB)
                </p>
                <img src={previewUrl} alt="Uploaded animal preview" className="preview-img" />
              </div>
            )}

            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={!selectedFile || uploading}>
                {uploading ? 'Processing...' : '1. Upload & Run Demo Image Screening'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={uploading}
                onClick={handleProceedToCombinedSymptoms}
              >
                {uploading ? 'Uploading...' : '2. Combine Image with Symptom Checker'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default ImageDetection
