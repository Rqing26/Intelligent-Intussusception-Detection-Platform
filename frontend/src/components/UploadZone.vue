<template>
  <div
    class="upload-zone"
    :class="{ 'is-dragover': isDragover, 'has-file': files.length, 'is-disabled': disabled }"
    role="group"
    aria-label="超声影像文件选择"
    :aria-disabled="disabled"
    @click="triggerInput"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
  >
    <input
      ref="fileInputRef"
      type="file"
      accept="image/jpeg,image/png,image/bmp,.dcm"
      multiple
      hidden
      :disabled="disabled"
      @click.stop
      @change="onFileChange"
    />

    <template v-if="!files.length">
      <div class="upload-illustration">
        <div class="upload-ring">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
        </div>
        <div class="upload-dots" />
      </div>
      <p class="upload-text">将超声影像拖放至此处</p>
      <p class="upload-hint">支持拖放文件，也可以从电脑中选择</p>
      <el-button class="choose-file-button" :icon="Plus" :disabled="disabled" @click.stop="triggerInput">选择影像</el-button>
      <div class="upload-formats">
        <span class="format-tag">JPG</span>
        <span class="format-tag">PNG</span>
        <span class="format-tag">BMP</span>
        <span class="format-tag">DICOM</span>
      </div>
      <p class="upload-limit">单个文件最大 20 MB</p>
      <p class="upload-dicom-note">DICOM 文件由算法侧解析用于诊断，浏览器暂不支持在线预览。</p>
    </template>

    <template v-else>
      <div class="file-list">
        <div v-for="(f, idx) in files" :key="f.uid" class="file-item">
          <div class="file-thumb">
            <img v-if="f.previewUrl" :src="f.previewUrl" class="thumb-img" alt="" />
            <el-icon v-else class="thumb-icon"><Document /></el-icon>
          </div>
          <div class="file-meta">
            <div class="file-name">{{ f.name }}</div>
            <div class="file-size">{{ formatSize(f.size) }}</div>
          </div>
          <button class="file-remove" type="button" title="移除" :disabled="disabled" :aria-label="`移除 ${f.name}`" @click.stop="removeFile(idx)">
            <el-icon><Close /></el-icon>
          </button>
        </div>
      </div>
      <div class="file-actions">
        <div><el-button :icon="Plus" :disabled="disabled" @click.stop="triggerInput">继续添加</el-button><el-button text :disabled="disabled" @click.stop="clearFiles">清空已选</el-button></div>
        <span class="file-count">已选 {{ files.length }} 张</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Plus, Document, Close } from '@element-plus/icons-vue'

const emit = defineEmits(['file-selected'])
const props = defineProps({ disabled: { type: Boolean, default: false } })

const isDragover = ref(false)
const files = ref([])
const fileInputRef = ref(null)

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/bmp', 'application/dicom']
const MAX_SIZE = 20 * 1024 * 1024
let uid = 0

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function validateFile(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_TYPES.includes(file.type) && ext !== 'dcm') {
    ElMessage.error(`不支持的文件类型：${file.name}`)
    return false
  }
  if (file.size > MAX_SIZE) {
    ElMessage.error(`文件超过 20MB 限制：${file.name}`)
    return false
  }
  return true
}

function addFiles(fileList) {
  if (props.disabled) return
  const arr = Array.from(fileList || [])
  for (const file of arr) {
    if (!validateFile(file)) continue
    // 支持图片预览；DICOM 等无法直接用 img 显示的用占位图标
    const previewUrl = file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/bmp'
      ? URL.createObjectURL(file)
      : ''
    files.value.push({ uid: ++uid, file, name: file.name, size: file.size, previewUrl })
  }
  emit('file-selected', files.value.map((f) => f.file))
}

function removeFile(idx) {
  if (props.disabled) return
  const f = files.value[idx]
  if (f && f.previewUrl) URL.revokeObjectURL(f.previewUrl)
  files.value.splice(idx, 1)
  emit('file-selected', files.value.map((x) => x.file))
}

function clearFiles() {
  if (props.disabled) return
  for (const f of files.value) {
    if (f.previewUrl) URL.revokeObjectURL(f.previewUrl)
  }
  files.value = []
  if (fileInputRef.value) fileInputRef.value.value = ''
  emit('file-selected', [])
}

function triggerInput() {
  if (props.disabled) return
  fileInputRef.value.click()
}

function onFileChange(e) {
  addFiles(e.target.files)
  e.target.value = ''
}

function onDragOver() {
  if (props.disabled) return
  isDragover.value = true
}

function onDragLeave() {
  isDragover.value = false
}

function onDrop(e) {
  isDragover.value = false
  addFiles(e.dataTransfer.files)
}

onUnmounted(() => {
  for (const f of files.value) {
    if (f.previewUrl) URL.revokeObjectURL(f.previewUrl)
  }
})
</script>

<style scoped>
.upload-zone {
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-lg);
  padding: 44px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-page);
  position: relative;
  overflow: hidden;
}
.upload-zone:hover {
  border-color: var(--primary);
  background: var(--bg-hover);
}
.upload-zone.is-disabled { cursor: default; }
.upload-zone.is-disabled:hover { background: var(--bg-page); border-color: var(--border-strong); }
.choose-file-button { height: 42px; margin: 0 0 22px; padding: 0 22px; color: var(--primary); border-color: var(--border-strong); background: var(--bg-card); }
.file-remove:disabled { cursor: not-allowed; opacity: .4; }
.upload-zone:focus-visible {
  outline: 3px solid var(--primary-glow);
  outline-offset: 4px;
  border-color: var(--primary);
}
.upload-zone.is-dragover {
  border-color: var(--primary);
  background: var(--primary-glow);
}

.upload-illustration {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 24px;
}
.upload-ring {
  width: 80px;
  height: 80px;
  border-radius: 26px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  box-shadow: 0 6px 16px rgba(23, 50, 57, 0.04);
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

.upload-text {
  margin: 0 0 6px;
  font-size: 17px;
  color: var(--text-primary);
  font-weight: 600;
}
.upload-hint {
  margin: 0 0 16px;
  font-size: 12px;
  line-height: 1.8;
  color: var(--text-muted);
}
.upload-dicom-note {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
}
.choose-file { color: var(--primary); font-weight: 600; }
.upload-limit { font-size: 11px; color: var(--text-muted); margin: 12px 0 0; }
.upload-formats {
  display: flex;
  gap: 8px;
  justify-content: center;
}
.format-tag {
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
}

/* 多文件列表 */
.file-list {
  width: 100%;
  max-width: 620px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}
.file-thumb {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}
.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumb-icon {
  font-size: 22px;
  color: var(--primary);
}
.file-meta {
  flex: 1;
  min-width: 0;
}
.file-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-size {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}
.file-remove {
  width: 30px;
  height: 30px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.file-remove:hover {
  background: var(--bg-tag-danger);
  color: var(--danger);
}
.file-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 620px;
  margin-top: 12px;
}
.file-count {
  font-size: 13px;
  color: var(--text-muted);
}
@media (max-width: 760px) {
  .upload-zone { min-height: 0; padding: 24px 16px; }
  .upload-illustration, .upload-ring { width: 48px; height: 48px; }
  .upload-illustration { margin-bottom: 14px; }
  .upload-ring { border-radius: 16px; }
  .upload-icon { font-size: 24px; }
  .upload-text { font-size: 15px; }
  .upload-hint { font-size: 11px; }
  .choose-file-button { height: 44px; margin-bottom: 16px; }
  .file-actions { flex-wrap: wrap; gap: 12px; }
  .file-actions .el-button, .file-remove { min-height: 44px; }
  .file-remove { min-width: 44px; }
}
</style>
