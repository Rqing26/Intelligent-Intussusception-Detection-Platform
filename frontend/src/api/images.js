import api from './index'

export function uploadImage(patientId, file, autoCrop = false) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('patient_id', patientId)
  if (autoCrop) fd.append('auto_crop', 'true')
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

// 去标识裁剪：mode = "auto"（模型自动去除患者信息条/参数栏/刻度条）
//            | "manual"（医生框选保留区，box = [x0, y0, x1, y1] 原图坐标）
export function cropImage(imageId, mode, box = null) {
  const payload = { mode }
  if (box) payload.box = box
  return api.post(`/images/${imageId}/crop`, payload)
}

export function runDetection(imageId, force = false) {
  return api.post(`/images/${imageId}/detect`, null, { params: { force } })
}

// 异步检测任务：提交后返回 task_id，需轮询 progress
export function createDetectionTask(imageId, force = false) {
  return api.post(`/detection/tasks/${imageId}`, null, { params: { force } })
}

export function getDetectionTask(taskId) {
  return api.get(`/detection/tasks/${taskId}`)
}

