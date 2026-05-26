import api from './index'

export function getSettings() {
  return api.get('/settings')
}

export function updateSettings(data) {
  return api.put('/settings', data)
}
