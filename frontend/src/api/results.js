import api from './index'

export function getResults(params) {
  return api.get('/results', { params })
}

export function getResult(id) {
  return api.get(`/results/${id}`)
}
