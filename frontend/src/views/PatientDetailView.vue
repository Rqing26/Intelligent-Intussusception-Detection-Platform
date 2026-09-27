<template>
  <AppLayout>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <h1 class="page-title">患者详情</h1>
        <p class="page-desc">查看患者信息、超声影像及检测结果</p>
      </div>
      <div class="page-header-actions">
        <el-button type="primary" @click="printLatestReport" v-if="patient">
          <el-icon><Printer /></el-icon>
          打印报告
        </el-button>
      </div>
    </div>

    <div v-loading="loading">
      <template v-if="patient">
        <div class="detail-layout">
          <!-- 左侧患者卡片 -->
          <div class="profile-panel">
            <div class="profile-card">
              <div class="profile-avatar" :style="{ background: stringToColor(patient.name) }">
                {{ patient.name?.charAt(0) || '?' }}
              </div>
              <div class="profile-name">{{ patient.name }}</div>
              <div class="profile-id">病历号 {{ patient.medical_record_no || '—' }}</div>

              <div class="profile-divider"></div>

              <div class="profile-meta">
                <div class="meta-row">
                  <span class="meta-label"><el-icon><User /></el-icon>性别</span>
                  <span class="meta-value">{{ patient.gender }}</span>
                </div>
                <div class="meta-row">
                  <span class="meta-label"><el-icon><Calendar /></el-icon>年龄</span>
                  <span class="meta-value">{{ patient.age }} 个月</span>
                </div>
                <div class="meta-row" v-if="patient.birth_date">
                  <span class="meta-label"><el-icon><Calendar /></el-icon>出生日期</span>
                  <span class="meta-value">{{ patient.birth_date }}</span>
                </div>
                <div class="meta-row" v-if="patient.medical_record_no">
                  <span class="meta-label"><el-icon><Document /></el-icon>病历号</span>
                  <span class="meta-value">{{ patient.medical_record_no }}</span>
                </div>
                <div class="meta-row" v-if="patient.hospital_no">
                  <span class="meta-label"><el-icon><OfficeBuilding /></el-icon>住院号</span>
                  <span class="meta-value">{{ patient.hospital_no }}</span>
                </div>
                <div class="meta-row" v-if="patient.exam_part">
                  <span class="meta-label"><el-icon><FirstAidKit /></el-icon>检查部位</span>
                  <span class="meta-value">{{ patient.exam_part }}</span>
                </div>
                <div class="meta-row">
                  <span class="meta-label"><el-icon><FirstAidKit /></el-icon>临床诊断</span>
                  <span class="meta-value">{{ patient.clinical_symptoms || '—' }}</span>
                </div>
                <div class="meta-row">
                  <span class="meta-label"><el-icon><Clock /></el-icon>录入时间</span>
                  <span class="meta-value">{{ formatDateTimeCn(patient.created_at) }}</span>
                </div>
              </div>

              <div class="profile-actions">
                <el-button
                  type="primary"
                  :icon="Upload"
                  @click="$router.push(`/patients/${patient.id}/upload`)"
                >
                  上传影像
                </el-button>
              </div>
            </div>
          </div>

          <!-- 右侧内容 -->
          <div class="detail-main">
            <!-- 统计网格 -->
            <div class="stats-grid">
              <div class="mini-stat">
                <div class="mini-stat-icon" style="--accent: var(--primary)">
                  <el-icon><Picture /></el-icon>
                </div>
                <div class="mini-stat-body">
                  <div class="mini-stat-value">{{ images.length }}</div>
                  <div class="mini-stat-label">影像数量</div>
                </div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-icon" style="--accent: var(--success)">
                  <el-icon><Select /></el-icon>
                </div>
                <div class="mini-stat-body">
                  <div class="mini-stat-value">{{ images.filter((i) => i.has_result).length }}</div>
                  <div class="mini-stat-label">检测次数</div>
                </div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-icon" style="--accent: var(--warning)">
                  <el-icon><DataLine /></el-icon>
                </div>
                <div class="mini-stat-body">
                  <div class="mini-stat-value" :style="latestResultStyle">{{ latestResultText }}</div>
                  <div class="mini-stat-label">最新结果</div>
                </div>
              </div>
            </div>

            <!-- 影像列表 -->
            <div class="data-card">
              <div class="card-header">
                <div class="card-header-left">
                  <div class="card-icon">
                    <el-icon><Picture /></el-icon>
                  </div>
                  <h3>超声影像列表</h3>
                </div>
                <el-button type="primary" @click="$router.push(`/patients/${patient.id}/upload`)">
                  + 上传新影像
                </el-button>
              </div>
              <div class="table-wrap">
                <el-table :data="images" class="image-table">
                  <template #empty>
                    <div class="empty-state">
                      <div class="empty-icon">
                        <el-icon :size="48"><Picture /></el-icon>
                      </div>
                      <p class="empty-title">暂无超声影像</p>
                      <p class="empty-desc">点击右上角按钮上传影像</p>
                    </div>
                  </template>

                  <el-table-column type="index" width="56" align="center">
                    <template #header>#</template>
                  </el-table-column>

                  <el-table-column prop="filename" label="文件名" min-width="180">
                    <template #default="{ row }">
                      <span class="filename-text">{{ row.filename }}</span>
                    </template>
                  </el-table-column>

                  <el-table-column label="上传时间" width="170">
                    <template #default="{ row }">
                      <div class="detect-time">
                        <el-icon><Clock /></el-icon>
                        <span>{{ formatDateTime(row.uploaded_at) }}</span>
                      </div>
                    </template>
                  </el-table-column>

                  <el-table-column label="状态" width="120" align="center">
                    <template #default="{ row }">
                      <span class="status-pill" :class="row.has_result ? 'status-success' : 'status-warning'">
                        <span class="status-dot"></span>
                        {{ row.has_result ? '已检测' : '待检测' }}
                      </span>
                    </template>
                  </el-table-column>

                  <el-table-column label="操作" width="180" fixed="right" align="center">
                    <template #default="{ row }">
                      <div class="action-group">
                        <el-tooltip content="预览" placement="top">
                          <button class="icon-btn" @click="previewImage(row)">
                            <el-icon><View /></el-icon>
                          </button>
                        </el-tooltip>
                        <el-tooltip v-if="!row.has_result" content="检测" placement="top">
                          <button class="icon-btn warn" @click="handleDetect(row)">
                            <el-icon><VideoPlay /></el-icon>
                          </button>
                        </el-tooltip>
                        <el-tooltip v-if="row.has_result" content="查看结果" placement="top">
                          <button class="icon-btn" @click="$router.push(`/results/${row.result_id}`)">
                            <el-icon><DataLine /></el-icon>
                          </button>
                        </el-tooltip>
                        <el-tooltip v-if="row.has_result" content="打印报告" placement="top">
                          <button class="icon-btn" @click="printForImage(row)">
                            <el-icon><Printer /></el-icon>
                          </button>
                        </el-tooltip>
                        <el-tooltip v-if="row.has_result" content="重新检测" placement="top">
                          <el-popconfirm
                            title="重新检测将覆盖当前结果，确认继续？"
                            confirm-button-text="重新检测"
                            cancel-button-text="取消"
                            @confirm="handleRedetect(row)"
                          >
                            <template #reference>
                              <button class="icon-btn warn">
                                <el-icon><RefreshRight /></el-icon>
                              </button>
                            </template>
                          </el-popconfirm>
                        </el-tooltip>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>

            <!-- 检测历史时间线：同一患者多次检测对比 -->
            <div class="data-card" v-if="detections.length">
              <div class="card-header">
                <div class="card-header-left">
                  <div class="card-icon">
                    <el-icon><DataLine /></el-icon>
                  </div>
                  <h3>检测历史（{{ detections.length }} 次）</h3>
                </div>
                <span class="timeline-hint">按时间倒序，对比历次诊断变化</span>
              </div>
              <div class="timeline-body">
                <div v-for="(d, idx) in detections" :key="d.id" class="timeline-item">
                  <div class="timeline-node" :class="detectionClass(d.classification)"></div>
                  <div class="timeline-card">
                    <div class="timeline-card-head">
                      <span class="tl-class" :class="detectionClass(d.classification)">{{ d.classification }}</span>
                      <span class="tl-conf">置信度 {{ Math.round((d.confidence || 0) * 100) }}%</span>
                      <span class="tl-time">{{ formatDateTime(d.created_at) }}</span>
                    </div>
                    <div class="timeline-card-body">
                      <span v-if="d.severity" class="tl-sev">等级：{{ d.severity }}</span>
                      <span v-if="d.treatment_success_rate != null" class="tl-sev">成功率 {{ Math.round(d.treatment_success_rate * 100) }}%</span>
                      <!-- 多模型溯源：检测(A) / 分类(B) / 预后 -->
                      <template v-if="d.detection_model_name || d.classification_model_name || d.prognosis_model_name">
                        <span v-if="d.detection_model_name" class="tl-model">检测 {{ d.detection_model_name }}<template v-if="d.detection_model_version"> v{{ d.detection_model_version }}</template></span>
                        <span v-if="d.classification_model_name" class="tl-model">分类 {{ d.classification_model_name }}<template v-if="d.classification_model_version"> v{{ d.classification_model_version }}</template></span>
                        <span v-if="d.prognosis_model_name" class="tl-model">预后 {{ d.prognosis_model_name }}<template v-if="d.prognosis_model_version"> v{{ d.prognosis_model_version }}</template></span>
                      </template>
                      <span v-else-if="d.model_name" class="tl-model">{{ d.model_name }}<template v-if="d.model_version"> v{{ d.model_version }}</template></span>
                    </div>
                    <div class="timeline-actions">
                      <el-button text size="small" @click="$router.push(`/results/${d.id}`)">查看详情</el-button>
                      <el-button text size="small" @click="openReportFor(d)">
                        <el-icon><Printer /></el-icon>打印
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 影像预览 -->
    <el-dialog v-model="previewVisible" title="影像预览" width="700px" append-to-body class="preview-dialog">
      <ImageViewer v-if="previewSrc" :src="previewSrc" :media-type="previewMediaType" />
    </el-dialog>

    <!-- 打印报告 -->
    <ReportPrint v-model="printVisible" :patient="patient" :result="printResult" :image-url="printImageUrl" />
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Printer,
  Upload,
  User,
  Calendar,
  Clock,
  FirstAidKit,
  Picture,
  Select,
  DataLine,
  View,
  VideoPlay,
  Document,
  OfficeBuilding,
  RefreshRight,
} from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import ImageViewer from '../components/ImageViewer.vue'
import ReportPrint from '../components/ReportPrint.vue'
import { getPatient } from '../api/patients'
import { getImageInfo, getImageUrl, runDetection, createDetectionTask, getDetectionTask } from '../api/images'
import { getResult, getResults, getResultImageUrl } from '../api/results'
import { formatDateTime, formatDateTimeCn } from '../utils/time'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const patient = ref(null)
const images = ref([])
const detections = ref([])
const previewVisible = ref(false)
const previewSrc = ref('')
const previewMediaType = ref('')
const printVisible = ref(false)
const printResult = ref(null)
const printImageUrl = ref('')

const latestDetection = computed(() => detections.value[0] || null)

const latestResultText = computed(() => {
  const d = latestDetection.value
  if (!d) return '—'
  let label = d.classification || '已检测'
  if (d.severity) label += ` · ${d.severity}`
  if (d.confidence != null) label += ` · ${Math.round(d.confidence * 100)}%`
  return label
})

const latestResultStyle = computed(() => {
  const cls = latestDetection.value?.classification
  if (cls === '肠套叠阳性') return { color: 'var(--danger)' }
  if (cls === '肠套叠阴性') return { color: 'var(--success)' }
  if (cls === '图像质量不佳') return { color: 'var(--warning)' }
  if (cls) return { color: 'var(--primary)' }
  return {}
})

function stringToColor(str) {
  if (!str) return 'var(--text-muted)'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#be185d', '#4338ca']
  return colors[Math.abs(hash) % colors.length]
}

function detectionClass(cls) {
  if (cls === '肠套叠阳性') return 'cls-positive'
  if (cls === '肠套叠阴性') return 'cls-negative'
  if (cls === '图像质量不佳') return 'cls-poor'
  return 'cls-default'
}

async function fetchPatient() {
  loading.value = true
  try {
    const id = route.params.id
    const res = await getPatient(id)
    patient.value = res.data
    if (patient.value.images) {
      images.value = await Promise.all(
        patient.value.images.map(async (img) => {
          try {
            const infoRes = await getImageInfo(img.id)
            return { ...img, has_result: infoRes.data.has_result, result_id: infoRes.data.result_id, media_type: infoRes.data.media_type }
          } catch {
            return { ...img, has_result: false, result_id: null, media_type: '' }
          }
        })
      )
    }
    // 获取该患者历次检测（时间趋势/前后对比）
    try {
      const r = await getResults({ patient_id: id, page: 1, size: 100 })
      detections.value = r.data.items ?? r.data.data ?? []
    } catch {
      detections.value = []
    }
  } catch {
    ElMessage.error('获取患者信息失败')
  } finally {
    loading.value = false
  }
}

function previewImage(row) {
  previewSrc.value = getImageUrl(row.id)
  previewMediaType.value = row.media_type || ''
  previewVisible.value = true
}

async function handleDetect(row, force = false) {
  try {
    // 使用异步任务 + 轮询，避免真实模型推理阻塞请求
    const taskRes = await createDetectionTask(row.id, force)
    const taskId = taskRes.data?.task_id
    let result
    if (taskId) {
      for (let i = 0; i < 180; i++) {
        const statusRes = await getDetectionTask(taskId)
        const t = statusRes.data?.task
        if (!t) break
        if (t.status === 'done') { result = statusRes.data?.result || { id: t.result_id }; break }
        if (t.status === 'failed') throw new Error(t.error || '检测失败')
        await new Promise((r) => setTimeout(r, 800))
      }
      if (!result) throw new Error('检测超时')
    } else {
      // 回退到同步接口
      const res = await runDetection(row.id, force)
      result = res.data
    }
    const resultId = result?.id ?? result?.result_id
    if (resultId) {
      ElMessage.success('检测完成')
      router.push(`/results/${resultId}`)
    } else {
      ElMessage.error('检测返回异常')
    }
  } catch (e) {
    ElMessage.error(e?.message || '检测失败')
  }
}

async function handleRedetect(row) {
  try {
    const res = await runDetection(row.id, true)
    const resultId = res.data?.id ?? res.data?.result_id
    if (resultId) {
      ElMessage.success('重新检测完成')
      await fetchPatient()
    } else {
      ElMessage.error('重新检测返回异常')
    }
  } catch (e) {
    ElMessage.error(e?.message || '重新检测失败')
  }
}

// 统一打开报告：按「结果 ID + 影像 ID」加载后打开打印预览
async function openReport(resultId, imageId) {
  if (!resultId) {
    ElMessage.warning('该记录暂无检测结果，无法打印报告')
    return
  }
  try {
    const res = await getResult(resultId)
    printResult.value = res.data
    // 报告优先用算法回传的标注图（带病灶框），没有则退回原图
    if (res.data?.has_result_image) {
      printImageUrl.value = getResultImageUrl(resultId)
    } else {
      // 优先用传入的影像 ID，其次用结果里的 image_id（历史记录只有后者）
      const imgId = imageId || res.data?.image_id
      printImageUrl.value = imgId ? getImageUrl(imgId) : ''
    }
    printVisible.value = true
  } catch {
    ElMessage.error('获取检测结果失败')
  }
}

// 影像列表行内打印
function printForImage(row) {
  return openReport(row.result_id, row.id)
}

// 检测历史时间线某条打印
function openReportFor(detection) {
  return openReport(detection.id, detection.image_id)
}

// 顶部「打印报告」：默认打印该患者【最近一次】检测结果
function printLatestReport() {
  if (detections.value.length) {
    const latest = detections.value[0]
    return openReport(latest.id, latest.image_id)
  }
  // 兜底：检测历史未取到时，从影像列表里找一条已检测的
  const withResult = images.value.find((i) => i.has_result && i.result_id)
  if (withResult) return openReport(withResult.result_id, withResult.id)
  ElMessage.warning('该患者暂无检测结果，请先上传影像并完成检测')
}

onMounted(fetchPatient)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
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
.page-header-actions {
  display: flex;
  gap: 10px;
}

/* 布局 */
.detail-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

/* 左侧患者卡片 */
.profile-panel {
  position: sticky;
  top: 20px;
  align-self: start;
}
.profile-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 28px 20px;
  text-align: center;
}
.profile-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 28px;
  font-weight: 700;
  font-family: var(--font-display);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.profile-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.profile-id {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-display);
  letter-spacing: 0.02em;
}
.profile-divider {
  height: 1px;
  background: var(--border-color);
  margin: 20px 0;
}
.profile-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: left;
}
.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}
.meta-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-weight: 500;
}
.meta-label .el-icon {
  font-size: 14px;
}
.meta-value {
  font-weight: 600;
  color: var(--text-primary);
  text-align: right;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.profile-actions {
  margin-top: 20px;
}
.profile-actions .el-button {
  width: 100%;
}

/* 右侧主内容 */
.detail-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 迷你统计 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.mini-stat {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.mini-stat:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}
.mini-stat-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  opacity: 0.1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mini-stat-icon .el-icon {
  color: var(--accent);
  font-size: 20px;
}
.mini-stat-value {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.mini-stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* 数据卡片 */
.data-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}
.card-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.card-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--primary-glow);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
}
.card-header h3 {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: 0.02em;
}

/* 表格 */
.table-wrap {
  padding: 0 4px;
  overflow-x: auto; /* 窄屏表格横向滚动，避免内容溢出 */
}
.image-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: var(--bg-page) !important;
  color: var(--text-secondary) !important;
  font-weight: 600 !important;
  font-size: 12px;
  border-bottom: 1px solid var(--border-color);
  padding: 12px 0;
}
.image-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: var(--bg-hover) !important;
}
.image-table :deep(td.el-table__cell) {
  padding: 14px 0;
  border-bottom: 1px solid var(--border-light);
}

.filename-text {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.detect-time {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}
.detect-time .el-icon {
  color: var(--text-muted);
  font-size: 14px;
}

/* 状态 pill */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-success {
  background: var(--bg-tag-success);
  color: var(--success);
}
.status-success .status-dot {
  background: var(--success);
}
.status-warning {
  background: var(--bg-tag-warning);
  color: var(--warning);
}
.status-warning .status-dot {
  background: var(--warning);
}

/* 操作按钮 */
.action-group {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.icon-btn {
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
  font-size: 15px;
}
.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--primary);
}
.icon-btn.warn:hover {
  background: var(--bg-tag-warning);
  color: var(--warning);
}

/* 空状态 */
.empty-state {
  padding: 50px 0;
  text-align: center;
}
.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--bg-hover);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  margin-bottom: 16px;
}
.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}
.empty-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

/* 预览弹窗 */
.preview-dialog :deep(.el-dialog__body) {
  padding: 0;
}

@media (max-width: 1100px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
  .profile-panel {
    position: static;
  }
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

/* 检测历史时间线 */
.timeline-hint {
  font-size: 12px;
  color: var(--text-muted);
}
.timeline-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: 520px;
  overflow-y: auto;
}
.timeline-item {
  position: relative;
  display: flex;
  gap: 16px;
  padding-left: 8px;
}
.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 12px;
  top: 20px;
  bottom: -6px;
  width: 2px;
  background: var(--border-color);
}
.timeline-node {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 8px;
  border: 2px solid var(--bg-card);
  box-shadow: 0 0 0 2px var(--border-color);
}
.timeline-node.cls-positive { background: var(--danger); }
.timeline-node.cls-negative { background: var(--success); }
.timeline-node.cls-poor { background: var(--warning); }
.timeline-node.cls-default { background: var(--primary); }
.timeline-card {
  flex: 1;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px 14px;
  margin-bottom: 14px;
}
.timeline-card-head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.tl-class {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
}
.tl-class.cls-positive { background: var(--bg-tag-danger); color: var(--danger); }
.tl-class.cls-negative { background: var(--bg-tag-success); color: var(--success); }
.tl-class.cls-poor { background: var(--bg-tag-warning); color: var(--warning); }
.tl-class.cls-default { background: var(--bg-tag-info); color: var(--primary); }
.tl-conf {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.tl-time {
  margin-left: auto;
  font-size: 12px;
  color: var(--text-muted);
}
.timeline-card-body {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.tl-sev {
  font-size: 12px;
  color: var(--text-secondary);
}
.tl-model {
  font-size: 11px;
  color: var(--text-muted);
}
.timeline-actions {
  margin-top: 8px;
}
</style>
