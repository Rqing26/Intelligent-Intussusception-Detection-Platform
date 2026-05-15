import api from './index'

export function getPatients(params) {
  return api.get('/patients', { params })
}

export function createPatient(data) {
  return api.post('/patients', data)
}

export function getPatient(id) {
  return api.get(`/patients/${id}`)
}

export function updatePatient(id, data) {
  return api.put(`/patients/${id}`, data)
}

export function deletePatient(id) {
  return api.delete(`/patients/${id}`)
}
