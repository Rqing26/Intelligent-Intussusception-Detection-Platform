import api from './index'

export function uploadImage(patientId, file) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('patient_id', patientId)
  return api.post('/images/upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getImageUrl(imageId) {
  return `/api/images/${imageId}`
}

export function getImageInfo(imageId) {
  return api.get(`/images/${imageId}/info`)
}

export function deleteImage(imageId) {
  return api.delete(`/images/${imageId}`)
}

export function runDetection(imageId) {
  return api.post(`/images/${imageId}/detect`)
}
