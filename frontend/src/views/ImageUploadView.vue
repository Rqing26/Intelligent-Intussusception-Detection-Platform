<template>
  <AppLayout>
    <div class="page-header-row">
      <div>
        <h2 class="page-title">上传影像</h2>
        <div class="breadcrumb">
          <span class="breadcrumb-link" @click="$router.push('/patients')">患者管理</span>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-link" @click="$router.push(`/patients/${patientId}`)">{{ patientName || '患者详情' }}</span>
          <span class="breadcrumb-sep">/</span>
          <span>上传影像</span>
        </div>
      </div>
    </div>

    <div class="upload-card">
      <div class="card-header">
        <h3>超声影像上传</h3>
        <p class="card-sub">请上传患儿腹部超声影像，系统将自动进行肠套叠检测分析</p>
      </div>
      <div class="card-body">
        <UploadZone @file-selected="onFileSelected" />
      </div>
      <div class="action-bar">
        <el-button
          type="primary"
          size="large"
          :disabled="!file"
          :loading="uploading"
          @click="handleUpload"
        >
          确认上传并检测
        </el-button>
        <el-button size="large" @click="$router.push(`/patients/${patientId}`)">取消</el-button>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppLayout from '../components/AppLayout.vue'
import UploadZone from '../components/UploadZone.vue'
import { uploadImage, runDetection } from '../api/images'

const route = useRoute()
const router = useRouter()

const patientId = computed(() => route.params.id)
const patientName = computed(() => route.query.name || '')
const file = ref(null)
const uploading = ref(false)

function onFileSelected(f) {
  file.value = f
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
.page-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-color);
}
.page-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.04em;
  margin: 0;
}
.breadcrumb {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
  font-style: italic;
}
.breadcrumb-link {
  cursor: pointer;
  transition: color 0.2s;
}
.breadcrumb-link:hover {
  color: var(--primary);
}
.breadcrumb-sep {
  margin: 0 6px;
  opacity: 0.5;
}

.upload-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  position: relative;
  max-width: 720px;
  margin: 0 auto;
}
.upload-card::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 24px;
  width: 48px;
  height: 2px;
  background: var(--gold);
}
.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}
.card-header h3 {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.06em;
  margin: 0 0 6px;
}
.card-sub {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
  font-style: italic;
}
.card-body {
  padding: 24px;
}
.action-bar {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
}
</style>
