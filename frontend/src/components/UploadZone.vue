<template>
  <div
    class="upload-zone"
    :class="{ 'is-dragover': isDragover, 'has-file': selectedFile }"
    @click="triggerInput"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <input
      ref="fileInputRef"
      type="file"
      accept="image/jpeg,image/png,image/bmp,.dcm"
      hidden
      @change="onFileChange"
    />

    <template v-if="!selectedFile">
      <div class="upload-illustration">
        <div class="upload-ring">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
        </div>
        <div class="upload-dots" />
      </div>
      <p class="upload-text">拖拽超声影像到此处，或点击选择文件</p>
      <p class="upload-hint">支持 JPG / PNG / BMP / DICOM 格式，单文件不超过 20MB</p>
      <div class="upload-formats">
        <span class="format-tag">JPG</span>
        <span class="format-tag">PNG</span>
        <span class="format-tag">BMP</span>
        <span class="format-tag">DICOM</span>
      </div>
    </template>

    <template v-else>
      <div class="preview-area">
        <img v-if="previewUrl" :src="previewUrl" class="preview-image" />
        <div class="preview-overlay">
          <div class="preview-info">
            <p class="preview-filename">{{ selectedFile.name }}</p>
            <p class="preview-size">{{ formatSize(selectedFile.size) }}</p>
          </div>
          <el-button size="small" type="primary" text bg @click.stop="clearFile">
            <el-icon><Refresh /></el-icon>
            重新选择
          </el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Refresh } from '@element-plus/icons-vue'

const emit = defineEmits(['file-selected'])

const isDragover = ref(false)
const selectedFile = ref(null)
const previewUrl = ref(null)
const fileInputRef = ref(null)

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/bmp', 'application/dicom']
const MAX_SIZE = 20 * 1024 * 1024

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function validateFile(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_TYPES.includes(file.type) && ext !== 'dcm') {
    ElMessage.error('不支持的文件类型，请上传 JPG/PNG/BMP/DICOM 文件')
    return false
  }
  if (file.size > MAX_SIZE) {
    ElMessage.error('文件大小超过 20MB 限制')
    return false
  }
  return true
}

function handleFile(file) {
  if (!validateFile(file)) return
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  emit('file-selected', file)
}

function triggerInput() {
  fileInputRef.value.click()
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (file) handleFile(file)
}

function onDragOver() {
  isDragover.value = true
}

function onDragLeave() {
  isDragover.value = false
}

function onDrop(e) {
  isDragover.value = false
  const file = e.dataTransfer.files[0]
  if (file) handleFile(file)
}

function clearFile() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  selectedFile.value = null
  previewUrl.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  emit('file-selected', null)
}
</script>

<style scoped>
.upload-zone {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  position: relative;
  overflow: hidden;
}

.upload-zone:hover {
  border-color: var(--primary);
  background: var(--bg-hover);
}

.upload-zone.is-dragover {
  border-color: var(--primary);
  background: var(--primary-glow);
  transform: scale(1.01);
}

/* 插图 */
.upload-illustration {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 16px;
}

.upload-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--primary-glow);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.upload-icon {
  font-size: 32px;
  color: var(--primary);
}

.upload-dots {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  background-image: radial-gradient(circle, var(--border-strong) 1.5px, transparent 1.5px);
  background-size: 8px 8px;
  opacity: 0.5;
}

/* 文字 */
.upload-text {
  margin: 0 0 6px;
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 600;
}

.upload-hint {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--text-muted);
}

/* 格式标签 */
.upload-formats {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.format-tag {
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-page);
  border: 1px solid var(--border-color);
}

/* 预览区域 */
.preview-area {
  position: relative;
  width: 100%;
  max-width: 400px;
}

.preview-image {
  width: 100%;
  max-height: 320px;
  object-fit: contain;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-page);
}

.preview-overlay {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview-info {
  text-align: center;
}

.preview-filename {
  margin: 0 0 2px;
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 600;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-size {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
