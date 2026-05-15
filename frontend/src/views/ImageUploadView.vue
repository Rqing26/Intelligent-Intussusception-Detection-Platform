<template>
  <AppLayout>
    <div class="image-upload">
      <el-page-header icon="" @back="$router.push(`/patients/${patientId}`)">
        <template #content>
          <span class="page-title">上传影像</span>
        </template>
      </el-page-header>

      <div class="content-wrapper">
        <UploadZone @file-selected="onFileSelected" />

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
        </div>
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
.image-upload {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.content-wrapper {
  margin-top: 20px;
  max-width: 600px;
}

.action-bar {
  margin-top: 24px;
  text-align: center;
}
</style>
