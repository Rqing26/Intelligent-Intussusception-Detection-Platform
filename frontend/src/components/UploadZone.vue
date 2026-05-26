<template>
  <div
    class="upload-zone"
    :class="{ 'is-dragover': isDragover }"
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
      <el-icon class="upload-icon"><UploadFilled /></el-icon>
      <p class="upload-text">拖拽超声影像到此处，或点击选择文件</p>
      <p class="upload-hint">支持 JPG/PNG/BMP/DICOM，不超过20MB</p>
    </template>
    <template v-else>
      <img v-if="previewUrl" :src="previewUrl" class="preview-image" />
      <p class="preview-filename">{{ selectedFile.name }}</p>
      <el-button size="small" type="primary" text @click.stop="clearFile">重新选择</el-button>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['file-selected'])

const isDragover = ref(false)
const selectedFile = ref(null)
const previewUrl = ref(null)
const fileInputRef = ref(null)

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/bmp', 'application/dicom']
const MAX_SIZE = 20 * 1024 * 1024

function validateFile(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_TYPES.includes(file.type) && ext !== 'dcm') {
    ElMessage.error('不支持的文件类型，请上传 JPG/PNG/BMP/DICOM 文件')
    return false
  }
  if (file.size > MAX_SIZE) {
    ElMessage.error('文件大小超过20MB限制')
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
}
</script>

<style scoped>
.upload-zone {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s, background-color 0.3s;
  min-height: 240px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-detail-item);
}

.upload-zone:hover,
.upload-zone.is-dragover {
  border-color: var(--gold);
  background: var(--bg-profile);
}

.upload-icon {
  font-size: 48px;
  color: var(--text-muted);
}

.upload-text {
  margin: 14px 0 6px;
  font-size: 15px;
  color: var(--text-secondary);
  font-weight: 600;
}

.upload-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  font-style: italic;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: var(--radius-lg);
  margin-bottom: 10px;
  border: 1px solid var(--border-color);
}

.preview-filename {
  margin: 6px 0;
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 600;
}
</style>
