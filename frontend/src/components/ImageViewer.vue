<template>
  <div class="image-viewer">
    <img
      v-if="!hasError"
      :src="src"
      :alt="alt"
      class="viewer-image"
      @error="hasError = true"
    />
    <div v-else class="viewer-error">
      <el-icon class="error-icon"><PictureFilled /></el-icon>
      <p class="error-text">图片加载失败</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: '' },
})

const hasError = ref(false)
</script>

<style scoped>
.image-viewer {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}

.viewer-image {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  display: block;
}

.viewer-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #909399;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 12px;
}

.error-text {
  margin: 0;
  font-size: 15px;
}
</style>
