import React, { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { ANIMALS } from './AnimalSelection'
import { uploadAnimalImage, predictAnimalImage } from '../services/api'

const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png']
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 // 5 MB

function ImageDetection() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const initialAnimal = searchParams.get('animal') || 'cow'
  const [animalId, setAnimalId] = useState(initialAnimal)
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadedInfo, setUploadedInfo] = useState(null)
  const [predictionResult, setPredictionResult] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  const currentAnimal = ANIMALS.find((a) => a.id === animalId) || ANIMALS[0]

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
    setUploadedInfo(null)
    setPredictionResult(null)

    if (!file) {
      setSelectedFile(null)
      setPreviewUrl('')
      return
    }

    const validationError = validateFile(file)
    if (validationError) {
      setErrorMsg(validationError)
      setSelectedFile(null)
      setPreviewUrl('')
      e.target.value = ''
      return
    }

    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
  }

  const handleUploadImage = async () => {
    if (!currentAnimal.aiSupported) {
      setErrorMsg(`AI image detection is not available for ${currentAnimal.name}.`)
      return null
    }
    if (!selectedFile) {
      setErrorMsg('Please select an animal image before uploading.')
      return null
    }

    setUploading(true)
    setErrorMsg('')
    setSuccessMsg('')

    try {
      const data = await uploadAnimalImage(selectedFile, currentAnimal.id)
      setUploadedInfo(data.upload)
      if (data.prediction) {
        setPredictionResult(data.prediction)
      }
      const shapeInfo = data.upload.preprocessedShape
        ? ` | Preprocessed tensor: [${data.upload.preprocessedShape.join(', ')}]`
        : ''
      setSuccessMsg(
        `Image uploaded to server (${data.upload.width}×${data.upload.height} ${data.upload.format}, ${data.upload.sizeKB} KB${shapeInfo}).`
      )
      return data
    } catch (err) {
      const serverError = err?.response?.data?.error
      if (serverError) {
        setErrorMsg(serverError)
      } else {
        setErrorMsg('Could not upload image to backend. Ensure the Flask server is running on port 5000.')
      }
      return null
    } finally {
      setUploading(false)
    }
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
      setUploadedInfo(uploadData)
      setPredictionResult(pred)

      navigate('/results', {
        state: {
          animal: currentAnimal.name,
          animalId: currentAnimal.id,
          imageName: uploadData.originalName || selectedFile.name,
          imagePath: uploadData.imagePath,
          previewUrl,
          imagePrediction: pred.imagePrediction,
          predictedClass: pred.predictedClass,
          confidence: pred.confidence,
          isLowConfidence: pred.isLowConfidence,
          uncertaintyNotice: pred.uncertaintyNotice,
          classProbabilities: pred.classProbabilities,
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
          'Could not run MobileNetV2 image prediction. Ensure the Flask server is running on port 5000.'
      )
    } finally {
      setUploading(false)
    }
  }

  const handleProceedToCombinedSymptoms = async () => {
    if (selectedFile && !predictionResult) {
      const uploaded = await handleUploadImage()
      if (!uploaded) {
        return
      }
      navigate(`/symptoms?animal=${currentAnimal.id}`, {
        state: {
          uploadedInfo: uploaded.upload,
          predictionResult: uploaded.prediction,
          previewUrl,
          imageName: uploaded.upload?.originalName || selectedFile.name
        }
      })
      return
    }

    navigate(`/symptoms?animal=${currentAnimal.id}`, {
      state: {
        uploadedInfo,
        predictionResult,
        previewUrl,
        imageName: uploadedInfo?.originalName || selectedFile?.name || null
      }
    })
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Image-Based Disease Detection</h1>
        <p>
          Upload a clear photograph of the animal (JPG, JPEG, or PNG, max 5 MB). Images are validated and prepared for 224 × 224 MobileNetV2 classification.
        </p>
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
                {a.emoji} {a.name} ({a.aiSupported ? 'AI Supported' : 'AI Unavailable'})
              </option>
            ))}
          </select>
        </div>

        {!currentAnimal.aiSupported ? (
          <div className="notice-warning">
            <p>
              <strong>AI Image Detection Unavailable for {currentAnimal.name}:</strong> Actual MobileNetV2 image classification is currently implemented only for <strong>Cow</strong> and <strong>Buffalo</strong>.
            </p>
            <div style={{ marginTop: '1rem' }}>
              <Link to={`/symptoms?animal=${currentAnimal.id}`} className="btn btn-secondary">
                Use Symptom Checker Instead
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleProceedToResults}>
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
              <button
                type="button"
                className="btn btn-secondary"
                disabled={!selectedFile || uploading}
                onClick={handleUploadImage}
              >
                {uploading ? 'Uploading...' : '1. Upload & Validate Image'}
              </button>
              <button type="submit" className="btn btn-primary" disabled={uploading}>
                {uploading ? 'Processing...' : '2. Upload & View Screening Result'}
              </button>
              <button
                type="button"
                className="btn btn-outline"
                disabled={uploading}
                onClick={handleProceedToCombinedSymptoms}
              >
                3. Also Select Symptoms (Combined Check)
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

export default ImageDetection
