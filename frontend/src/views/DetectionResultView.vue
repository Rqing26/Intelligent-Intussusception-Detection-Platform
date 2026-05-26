<template>
  <AppLayout>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <h1 class="page-title">检测结果</h1>
        <p class="page-desc">查看AI辅助诊断结果与影像分析详情</p>
      </div>
      <div class="page-header-actions">
        <el-button type="primary" @click="printVisible = true" v-if="result">
          <el-icon><Printer /></el-icon>
          打印报告
        </el-button>
      </div>
    </div>

    <div v-loading="loading">
      <template v-if="result">
        <!-- 患者信息条 -->
        <div class="patient-bar">
          <div class="patient-bar-item">
            <div class="bar-label">患者</div>
            <div class="bar-value">
              <span v-if="patient">{{ patient.name }} · {{ patient.age }}个月 · {{ patient.gender }}</span>
              <span v-else>—</span>
            </div>
          </div>
          <div class="patient-bar-divider"></div>
          <div class="patient-bar-item">
            <div class="bar-label">检测时间</div>
            <div class="bar-value">{{ result.created_at }}</div>
          </div>
          <div class="patient-bar-divider"></div>
          <div class="patient-bar-item">
            <div class="bar-label">诊断分类</div>
            <div class="bar-value">
              <span class="mini-badge" :class="classificationClass">{{ result.classification }}</span>
            </div>
          </div>
        </div>

        <!-- 结果网格 -->
        <div class="result-layout">
          <!-- 左侧影像 -->
          <div class="result-panel image-panel">
            <div class="panel-header">
              <div class="panel-icon">
                <el-icon><Picture /></el-icon>
              </div>
              <h3>超声影像</h3>
            </div>
            <div class="panel-body image-body">
              <ImageViewer :src="imageUrl" alt="超声影像" />
            </div>
          </div>

          <!-- 右侧诊断 -->
          <div class="result-panel diag-panel">
            <div class="panel-header">
              <div class="panel-icon">
                <el-icon><DataLine /></el-icon>
              </div>
              <h3>AI 诊断分析</h3>
            </div>
            <div class="panel-body">
              <ResultCard :result="result" />
            </div>
          </div>
        </div>
      </template>
    </div>

    <ReportPrint v-model="printVisible" :patient="patient" :result="result" :image-url="imageUrl" />
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Printer, Picture, DataLine } from '@element-plus/icons-vue'
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

const classificationClass = computed(() => {
  const map = {
    '肠套叠阳性': 'badge-danger',
    '肠套叠阴性': 'badge-success',
    '图像质量不佳': 'badge-warning',
  }
  return map[result.value?.classification] || ''
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
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
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
.page-header-actions {
  display: flex;
  gap: 10px;
}

/* 患者信息条 */
.patient-bar {
  display: inline-flex;
  align-items: center;
  gap: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 14px 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
}
.patient-bar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
}
.patient-bar-item:first-child {
  padding-left: 0;
}
.patient-bar-item:last-child {
  padding-right: 0;
}
.patient-bar-divider {
  width: 1px;
  height: 24px;
  background: var(--border-color);
}
.bar-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}
.bar-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.mini-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.badge-danger {
  background: var(--bg-tag-danger);
  color: var(--danger);
}
.badge-success {
  background: var(--bg-tag-success);
  color: var(--success);
}
.badge-warning {
  background: var(--bg-tag-warning);
  color: var(--warning);
}

/* 结果布局 */
.result-layout {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 20px;
}
.result-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
}
.panel-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--primary-glow);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}
.panel-header h3 {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: 0.02em;
}
.panel-body {
  padding: 18px;
  flex: 1;
}
.image-body {
  padding: 0;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-hover);
}

@media (max-width: 1100px) {
  .result-layout {
    grid-template-columns: 1fr;
  }
  .patient-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .patient-bar-divider {
    display: none;
  }
  .patient-bar-item {
    padding: 0;
  }
}
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
