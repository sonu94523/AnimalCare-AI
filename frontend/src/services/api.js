import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
const DEFAULT_ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || ''

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000
})

function adminHeaders(tokenOverride) {
  const token = (tokenOverride ?? DEFAULT_ADMIN_TOKEN).trim()
  return token ? { 'X-Admin-Token': token } : {}
}

export async function checkBackendHealth() {
  const response = await apiClient.get('/api/health')
  return response.data
}

export async function fetchAnimals() {
  const response = await apiClient.get('/api/animals')
  return response.data.animals
}

export async function fetchSymptoms(animalId = '') {
  const params = animalId ? { animal: animalId } : {}
  const response = await apiClient.get('/api/symptoms', { params })
  return response.data.symptoms
}

export async function submitSymptomForm(animalId, symptoms) {
  const response = await apiClient.post('/api/symptoms/submit', {
    animal: animalId,
    symptoms
  })
  return response.data
}

export async function fetchDiseases() {
  const response = await apiClient.get('/api/diseases')
  return response.data.diseases
}

export async function fetchHistory(animalFilter = '') {
  const params = animalFilter && animalFilter !== 'all' ? { animal: animalFilter } : {}
  const response = await apiClient.get('/api/history', { params })
  return response.data.records
}

export async function deleteHistoryRecord(recordId, adminToken) {
  const response = await apiClient.delete(`/api/history/${recordId}`, {
    headers: adminHeaders(adminToken)
  })
  return response.data
}

export async function clearAllHistory(adminToken) {
  const response = await apiClient.delete('/api/history', {
    headers: adminHeaders(adminToken)
  })
  return response.data
}

export async function fetchModelInfo() {
  const response = await apiClient.get('/api/model/info')
  return response.data
}

export async function uploadAnimalImage(file, animalId) {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('animal', animalId)

  const response = await apiClient.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

export async function predictAnimalImage(file, animalId) {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('animal', animalId)

  const response = await apiClient.post('/api/predict/image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

export async function submitCombinedPrediction({ animal, symptoms, uploadId }) {
  const payload = { animal, symptoms }
  if (uploadId) {
    payload.uploadId = uploadId
  }
  const response = await apiClient.post('/api/predict/combined', payload)
  return response.data
}
