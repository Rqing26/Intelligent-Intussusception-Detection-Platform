<template>
  <AppLayout>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <h1 class="page-title">上传影像</h1>
        <p class="page-desc">上传患儿腹部超声影像，系统将自动进行肠套叠检测分析</p>
      </div>
    </div>

    <!-- 上传卡片 -->
    <div class="upload-layout">
      <div class="upload-card">
        <div class="card-header">
          <div class="header-icon">
            <el-icon :size="28"><Upload /></el-icon>
          </div>
          <div class="header-text">
            <h3>超声影像上传</h3>
            <p>支持 JPG、PNG、DICOM 格式，单文件不超过 20MB</p>
          </div>
        </div>

        <div class="card-body">
          <UploadZone @file-selected="onFileSelected" />

          <div v-if="file" class="file-preview">
            <div class="file-info">
              <div class="file-icon">
                <el-icon :size="24"><Document /></el-icon>
              </div>
              <div class="file-meta">
                <div class="file-name">{{ file.name }}</div>
                <div class="file-size">{{ formatFileSize(file.size) }}</div>
              </div>
            </div>
            <button class="file-remove" @click="file = null">
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </div>

        <div class="action-bar">
          <el-button size="large" @click="$router.push(`/patients/${patientId}`)">
            取消
          </el-button>
          <el-button
            type="primary"
            size="large"
            :disabled="!file"
            :loading="uploading"
            @click="handleUpload"
          >
            <span v-if="uploading">上传检测中...</span>
            <span v-else>确认上传并检测</span>
          </el-button>
        </div>
      </div>

      <!-- 提示卡片 -->
      <div class="tips-card">
        <div class="tips-title">
          <el-icon><InfoFilled /></el-icon>
          上传注意事项
        </div>
        <ul class="tips-list">
          <li>
            <span class="tip-num">1</span>
            请确保超声影像清晰，肠管结构可辨识
          </li>
          <li>
            <span class="tip-num">2</span>
            建议上传腹部纵切面和横切面两张影像
          </li>
          <li>
            <span class="tip-num">3</span>
            影像中应包含标尺和探头位置标记
          </li>
          <li>
            <span class="tip-num">4</span>
            上传后系统将自动进行AI检测分析
          </li>
        </ul>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, Document, Close, InfoFilled } from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import UploadZone from '../components/UploadZone.vue'
import { uploadImage, runDetection } from '../api/images'

const route = useRoute()
const router = useRouter()

const patientId = computed(() => route.params.id)
const file = ref(null)
const uploading = ref(false)

function onFileSelected(f) {
  file.value = f
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

async function handleUpload() {
  if (!file.value) return
  uploading.value = true
  try {
    const uploadRes = await uploadImage(patientId.value, file.value)
    const imageId = uploadRes.data.id ?? uploadRes.data.image_id
    if (!imageId) {
      ElMessage.error('上传响应异常')
      return
    }
    const detectRes = await runDetection(imageId)
    const resultId = detectRes.data.id ?? detectRes.data.result_id
    if (resultId) {
      ElMessage.success('上传并检测成功')
      router.push(`/results/${resultId}`)
    } else {
      ElMessage.error('检测响应异常')
    }
  } catch {
    ElMessage.error('上传或检测失败')
  } finally {
    uploading.value = false
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.02em;
  margin: 0 0 4px;
}
.page-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

/* 布局 */
.upload-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  align-items: start;
}

/* 上传卡片 */
.upload-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
}
.header-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  background: var(--primary-glow);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.header-text h3 {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px;
}
.header-text p {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

.card-body {
  padding: 24px;
}

/* 文件预览 */
.file-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding: 14px 16px;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}
.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.file-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  flex-shrink: 0;
}
.file-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  max-width: 300px;
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
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.file-remove:hover {
  background: var(--bg-tag-danger);
  color: var(--danger);
}

/* 操作栏 */
.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-page);
}

/* 提示卡片 */
.tips-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
  position: sticky;
  top: 20px;
}
.tips-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}
.tips-title .el-icon {
  color: var(--primary);
}
.tips-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.tips-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
.tip-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--primary-glow);
  color: var(--primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 1px;
}

@media (max-width: 900px) {
  .upload-layout {
    grid-template-columns: 1fr;
  }
  .tips-card {
    position: static;
  }
}
@media (max-width: 480px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .action-bar {
    flex-direction: column;
  }
  .action-bar .el-button {
    width: 100%;
  }
}
</style>
