<template>
  <AppLayout>
    <div class="detection-result">
      <el-page-header icon="" @back="$router.push('/patients')">
        <template #content>
          <span class="page-title">检测结果</span>
        </template>
      </el-page-header>

      <div class="content-wrapper" v-loading="loading">
        <template v-if="result">
          <p class="detect-time" v-if="result.created_at">
            检测时间：{{ result.created_at }}
          </p>

          <div class="result-grid">
            <div class="result-left">
              <ImageViewer :src="imageUrl" alt="超声影像" />
            </div>
            <div class="result-right">
              <ResultCard :result="result" />
            </div>
          </div>
        </template>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppLayout from '../components/AppLayout.vue'
import ImageViewer from '../components/ImageViewer.vue'
import ResultCard from '../components/ResultCard.vue'
import { getResult } from '../api/results'
import { getImageUrl } from '../api/images'

const route = useRoute()
const loading = ref(false)
const result = ref(null)

const imageUrl = computed(() => {
  if (result.value && result.value.image_id) {
    return getImageUrl(result.value.image_id)
  }
  return ''
})

async function fetchResult() {
  loading.value = true
  try {
    const res = await getResult(route.params.id)
    result.value = res.data
  } catch {
    ElMessage.error('获取检测结果失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchResult)
</script>

<style scoped>
.detection-result {
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
}

.detect-time {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.result-left {
  min-height: 300px;
}

.result-right {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}
</style>
