<template>
  <div class="image-viewer">
    <img
      v-if="!hasError && resolvedSrc"
      :src="resolvedSrc"
      :alt="alt"
      class="viewer-image"
      @error="hasError = true"
    />
    <div v-else-if="hasError" class="viewer-error">
      <el-icon class="error-icon"><PictureFilled /></el-icon>
      <p class="error-text">图片加载失败</p>
    </div>
    <div v-else class="viewer-loading">
      <el-icon class="loading-icon is-loading"><Loading /></el-icon>
      <p class="loading-text">加载中...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { PictureFilled, Loading } from '@element-plus/icons-vue'
import api from '../api/index'

const props = defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: '' },
})

const hasError = ref(false)
const resolvedSrc = ref('')
let objectUrl = null

const loadImage = async (url) => {
  hasError.value = false
  resolvedSrc.value = ''

  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = null
  }

  if (!url) return

  if (url.startsWith('/api/')) {
    try {
      const requestUrl = url.replace(/^\/api/, '')
      const response = await api.get(requestUrl, { responseType: 'blob' })
      objectUrl = URL.createObjectURL(response.data)
      resolvedSrc.value = objectUrl
    } catch (e) {
      hasError.value = true
    }
  } else {
    resolvedSrc.value = url
  }
}

watch(() => props.src, (newVal) => {
  loadImage(newVal)
}, { immediate: true })

onUnmounted(() => {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
  }
})
</script>

<style scoped>
.image-viewer {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 360px;
  background: var(--bg-detail-item);
  overflow: hidden;
  width: 100%;
  height: 100%;
}

.viewer-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  max-width: 100%;
  max-height: 560px;
  display: block;
}

.viewer-error, .viewer-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--text-muted);
  padding: 60px 0;
}

.error-icon, .loading-icon {
  font-size: 64px;
  margin-bottom: 12px;
}

.error-text, .loading-text {
  margin: 0;
  font-size: 15px;
  font-family: var(--font-sans);
}
</style>
