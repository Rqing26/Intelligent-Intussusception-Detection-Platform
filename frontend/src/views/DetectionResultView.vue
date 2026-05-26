<template>
  <AppLayout>
    <div class="page-header-row">
      <div>
        <h2 class="page-title">检测结果</h2>
        <div class="breadcrumb">
          <span class="breadcrumb-link" @click="$router.push('/patients')">患者管理</span>
          <span class="breadcrumb-sep">/</span>
          <span class="breadcrumb-link" @click="$router.push(`/patients/${patient?.id}`)" v-if="patient">{{ patient.name }}</span>
          <span class="breadcrumb-sep" v-if="patient">/</span>
          <span>检测结果</span>
        </div>
      </div>
      <el-button type="primary" @click="printVisible = true" v-if="result">
        <el-icon><Printer /></el-icon>打印报告
      </el-button>
    </div>

    <div v-loading="loading">
      <template v-if="result">
        <div class="result-meta-bar">
          <div class="meta-item">
            <span class="meta-label">检测时间</span>
            <span class="meta-value">{{ result.created_at }}</span>
          </div>
          <div class="meta-item" v-if="patient">
            <span class="meta-label">患者</span>
            <span class="meta-value">{{ patient.name }} · {{ patient.age }}个月 · {{ patient.gender }}</span>
          </div>
        </div>

        <div class="result-grid">
          <div class="result-left card">
            <div class="card-header small">
              <h3>超声影像</h3>
            </div>
            <div class="card-body image-body">
              <ImageViewer :src="imageUrl" alt="超声影像" />
            </div>
          </div>
          <div class="result-right card">
            <div class="card-header small">
              <h3>AI 诊断分析</h3>
            </div>
            <div class="card-body">
              <ResultCard :result="result" />
            </div>
          </div>
        </div>
      </template>
    </div>

    <ReportPrint
      v-model="printVisible"
      :patient="patient"
      :result="result"
      :image-url="imageUrl"
    />
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppLayout from '../components/AppLayout.vue'
import ImageViewer from '../components/ImageViewer.vue'
import ResultCard from '../components/ResultCard.vue'
import ReportPrint from '../components/ReportPrint.vue'
import { getResult } from '../api/results'
import { getImageUrl } from '../api/images'
import { getPatient } from '../api/patients'

const route = useRoute()
const loading = ref(false)
const result = ref(null)
const patient = ref(null)
const printVisible = ref(false)

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
    if (result.value.image) {
      const imgInfo = result.value.image
      try {
        const pRes = await getPatient(imgInfo.patient_id)
        patient.value = pRes.data
      } catch {
        patient.value = null
      }
    }
  } catch {
    ElMessage.error('获取检测结果失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchResult)
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

.result-meta-bar {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.meta-label {
  color: var(--text-muted);
  font-family: var(--font-display);
  letter-spacing: 0.04em;
}
.meta-value {
  color: var(--text-primary);
  font-weight: 600;
}

.result-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 20px;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  position: relative;
}
.card::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 20px;
  width: 40px;
  height: 2px;
  background: var(--gold);
}
.card-header.small {
  display: flex;
  align-items: center;
  padding: 12px 18px;
  border-bottom: 1px solid var(--border-color);
}
.card-header.small h3 {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.06em;
  margin: 0;
}
.card-body {
  padding: 18px;
}
.image-body {
  padding: 0;
  min-height: 360px;
}

@media (max-width: 1100px) {
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
