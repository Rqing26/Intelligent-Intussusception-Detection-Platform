<template>
  <AppLayout>
    <button class="page-back-link" type="button" @click="handleBack">
      <el-icon><Back /></el-icon>
      {{ patientId ? '返回患者档案' : '返回上一页' }}
    </button>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <span class="page-eyebrow">ANALYSIS REPORT</span>
        <h1 class="page-title">检测结果</h1>
        <p class="page-desc">超声影像与 AI 辅助分析，在同一视野中清晰呈现。</p>
      </div>
      <div class="page-header-actions" v-if="result">
        <el-button v-if="patientId" :icon="Upload" @click="$router.push(`/patients/${patientId}/upload`)">
          继续上传检测
        </el-button>
        <el-button type="primary" :icon="Printer" @click="printVisible = true">
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
            <div class="bar-value">{{ formatDateTime(result.created_at) }}</div>
          </div>
          <div class="patient-bar-divider"></div>
          <div class="patient-bar-item">
            <div class="bar-label">诊断分类</div>
            <div class="bar-value">
              <span class="mini-badge" :class="classificationClass">{{ result.classification }}</span>
            </div>
          </div>
          <div class="patient-bar-divider"></div>
          <div class="patient-bar-item">
            <div class="bar-label">模型</div>
            <!-- 多模型溯源：有哪个模型就显示哪一行
                 （检测=病灶在哪 / 分类=有没有肠套叠 / 预后=灌肠复位会不会成功） -->
            <div class="bar-value model-value" v-if="hasNamedModels">
              <span v-if="result.detection_model_name" class="model-line">
                <span class="model-role">检测</span>
                <span class="model-name">{{ result.detection_model_name }}<template v-if="result.detection_model_version"> v{{ result.detection_model_version }}</template></span>
                <span v-if="result.detection_ms != null" class="model-meta">{{ result.detection_ms }}ms</span>
                <span v-if="result.detection_score != null" class="model-meta">证据分 {{ result.detection_score.toFixed(3) }}</span>
              </span>
              <span v-if="result.classification_model_name" class="model-line">
                <span class="model-role">分类</span>
                <span class="model-name">{{ result.classification_model_name }}<template v-if="result.classification_model_version"> v{{ result.classification_model_version }}</template></span>
                <span v-if="result.classification_ms != null" class="model-meta">{{ result.classification_ms }}ms</span>
              </span>
              <span v-if="result.prognosis_model_name" class="model-line">
                <span class="model-role model-role-prognosis">预后</span>
                <span class="model-name">{{ result.prognosis_model_name }}<template v-if="result.prognosis_model_version"> v{{ result.prognosis_model_version }}</template></span>
                <span v-if="result.prognosis_ms != null" class="model-meta">{{ result.prognosis_ms }}ms</span>
              </span>
            </div>
            <!-- 旧数据 / Mock 回退：只有一个整体模型名 -->
            <div class="bar-value" v-else>{{ legacyModelText }}</div>
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
              <!-- 算法回传了标注图时，提供 原图 / 标注图 切换 -->
              <el-radio-group v-if="hasAnnotatedImage" v-model="imageMode" size="small" class="image-mode-switch">
                <el-radio-button value="original">原图</el-radio-button>
                <el-radio-button value="annotated">AI 标注图</el-radio-button>
              </el-radio-group>
              <span v-else-if="hasBoxOverlay" class="image-mode-hint">已叠加 AI 病灶框</span>
            </div>
            <div class="panel-body image-body">
              <ImageViewer
                :src="displayImageUrl"
                alt="超声影像"
                :media-type="displayMediaType"
                :overlay-box="overlayBox"
              />
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

    <ReportPrint v-model="printVisible" :patient="patient" :result="result" :image-url="reportImageUrl" />
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Printer, Picture, DataLine, Back, Upload } from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import ImageViewer from '../components/ImageViewer.vue'
import ResultCard from '../components/ResultCard.vue'
import ReportPrint from '../components/ReportPrint.vue'
import { getResult, getResultImageUrl } from '../api/results'
import { getImageUrl } from '../api/images'
import { getPatient } from '../api/patients'
import { formatDateTime } from '../utils/time'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const result = ref(null)
const patient = ref(null)
const printVisible = ref(false)
const imageMode = ref('original')
const patientId = computed(() => result.value?.image?.patient_id || patient.value?.id)

// 返回患者详情（结果中的影像包含 patient_id）；若无则返回上一页
function handleBack() {
  const pid = patientId.value
  if (pid) router.push(`/patients/${pid}`)
  else router.back()
}

const imageUrl = computed(() => {
  if (result.value && result.value.image_id) {
    return getImageUrl(result.value.image_id)
  }
  return ''
})

// ---- 多模型溯源 ----
const hasNamedModels = computed(() => Boolean(
  result.value?.detection_model_name
  || result.value?.classification_model_name
  || result.value?.prognosis_model_name
))

const legacyModelText = computed(() => {
  const r = result.value
  if (!r) return '—'
  let text = r.model_name || '—'
  if (r.model_version) text += ` v${r.model_version}`
  if (r.inference_ms != null) text += ` · ${r.inference_ms}ms`
  return text
})

// ---- 影像：原图 / AI 标注图 ----
const hasAnnotatedImage = computed(() => Boolean(result.value?.has_result_image))
// 算法只给了病灶框坐标（没给标注图）时，前端在原图上叠加展示
const boxOverlay = computed(() => (hasAnnotatedImage.value ? null : (result.value?.roi_box || null)))
const hasBoxOverlay = computed(() => Array.isArray(boxOverlay.value))
const overlayBox = computed(() => boxOverlay.value)

const displayImageUrl = computed(() => {
  if (imageMode.value === 'annotated' && hasAnnotatedImage.value) {
    return getResultImageUrl(result.value.id)
  }
  return imageUrl.value
})

// 标注图一定是普通图片；原图可能是 DICOM（不可在线预览）
const displayMediaType = computed(() => {
  if (imageMode.value === 'annotated' && hasAnnotatedImage.value) return ''
  return result.value?.image?.media_type || ''
})

// 报告优先用标注图，其次用原图
const reportImageUrl = computed(() => (
  hasAnnotatedImage.value ? getResultImageUrl(result.value.id) : imageUrl.value
))

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
    // 原图是 DICOM 时浏览器无法预览，若算法给了标注图则默认展示标注图
    if (hasAnnotatedImage.value && result.value?.image?.media_type === 'application/dicom') {
      imageMode.value = 'annotated'
    }
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
.page-back-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 36px;
  margin: -8px 0 14px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--text-secondary);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.page-back-link:hover { color: var(--primary); }
.page-back-link:focus-visible { outline: 2px solid var(--primary); outline-offset: 4px; border-radius: 4px; }
.page-eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--primary);
}

.page-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 28px;
}
.page-title {
  font-family: var(--font-display);
  font-size: clamp(26px, 2.5vw, 32px);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.04em;
  line-height: 1.3;
  margin: 7px 0 9px;
}
.page-desc {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-muted);
  margin: 0;
}
.page-header-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  margin-left: auto;
  gap: 10px;
}
.page-header-actions .el-button { min-height: 42px; padding: 0 18px; margin-left: 0; }

/* 患者信息条 */
.patient-bar {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr minmax(220px, 1.5fr);
  gap: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 24px;
}
.patient-bar-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
  gap: 10px;
  padding: 0 20px;
  border-right: 1px solid var(--border-light);
}
.patient-bar-item:first-child {
  padding-left: 0;
}
.patient-bar-item:last-child {
  padding-right: 0;
  border-right: 0;
}
.patient-bar-divider {
  display: none;
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
  line-height: 1.65;
  overflow-wrap: anywhere;
}

/* 双模型：检测 / 分类 各一行 */
.model-value {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-weight: 500;
}
.model-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  line-height: 1.6;
}
.model-role {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  padding: 0 6px;
  height: 18px;
  border-radius: 4px;
  background: var(--primary-glow);
  color: var(--primary);
  font-size: 11px;
  font-weight: 600;
}
/* 预后模型用不同底色区分，避免和"诊断分类"混淆 */
.model-role-prognosis {
  background: var(--bg-tag-warning, #fdf6ec);
  color: var(--warning, #e6a23c);
}
.model-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}
.model-meta {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
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
  grid-template-columns: minmax(0, 1.15fr) minmax(340px, 0.85fr);
  gap: 24px;
  align-items: start;
}
.result-panel {
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 24px rgba(23, 50, 57, 0.025);
}
.panel-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  min-height: 80px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
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
/* 影像面板右上角：原图 / AI 标注图 切换 */
.image-mode-switch {
  margin-left: auto;
}
.image-mode-hint {
  margin-left: auto;
  font-size: 12px;
  color: var(--primary);
  background: var(--primary-glow);
  padding: 2px 10px;
  border-radius: 10px;
}
.panel-body {
  padding: 24px;
  flex: 1;
}
.image-body {
  padding: 20px;
  min-height: 460px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #15272c;
}

@media (max-width: 1200px) {
  .patient-bar { grid-template-columns: 1fr 1fr; gap: 24px; }
  .patient-bar-item { padding: 0; border: 0; }
}
@media (max-width: 1000px) {
  .result-layout { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 16px; }
  .patient-bar { grid-template-columns: 1fr; padding: 20px; gap: 18px; }
  .patient-bar-item { gap: 4px; }
  .panel-header, .panel-body { padding: 18px; }
  .image-body { min-height: 300px; padding: 8px; }
  .page-header-actions { width: 100%; margin-left: 0; }
  .page-header-actions .el-button { flex: 1 1 150px; }
  .image-mode-switch { margin-left: 0; }
}
</style>
