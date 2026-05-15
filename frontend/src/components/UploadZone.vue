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
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s, background-color 0.3s;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-zone:hover,
.upload-zone.is-dragover {
  border-color: #409EFF;
  background: #ecf5ff;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
}

.upload-text {
  margin: 12px 0 4px;
  font-size: 15px;
  color: #606266;
}

.upload-hint {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  margin-bottom: 8px;
}

.preview-filename {
  margin: 4px 0;
  font-size: 14px;
  color: #303133;
}
</style>
