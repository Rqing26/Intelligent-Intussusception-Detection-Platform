<template>
  <AppLayout>
    <router-link class="page-back-link" to="/patients">
      <el-icon><Back /></el-icon>
      返回患者列表
    </router-link>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <span class="page-eyebrow">PATIENT PROFILE</span>
        <h1 class="page-title">患者详情</h1>
        <p class="page-desc">查看患者信息、超声影像及检测结果</p>
      </div>
      <div class="page-header-actions" v-if="patient">
        <el-button :icon="Printer" :disabled="loading || !hasPrintableResult" :title="hasPrintableResult ? '打印最近一次检测报告' : '完成检测后可打印报告'" @click="printLatestReport">
          打印最新报告
        </el-button>
        <el-button type="primary" :icon="Upload" @click="$router.push(`/patients/${patient.id}/upload`)">
          上传影像并检测
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
            </div>
          </div>

          <!-- 右侧内容 -->
          <div class="detail-main">
            <!-- 统计网格 -->
            <div class="stats-grid">
              <div class="mini-stat">
                <div class="mini-stat-icon" style="--accent: var(--primary); --accent-tint: var(--bg-tag-info)">
                  <el-icon><Picture /></el-icon>
                </div>
                <div class="mini-stat-body">
                  <div class="mini-stat-value">{{ images.length }}</div>
                  <div class="mini-stat-label">影像数量</div>
                </div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-icon" style="--accent: var(--success); --accent-tint: var(--bg-tag-success)">
                  <el-icon><Select /></el-icon>
                </div>
                <div class="mini-stat-body">
                  <div class="mini-stat-value">{{ images.filter((i) => i.has_result).length }}</div>
                  <div class="mini-stat-label">检测次数</div>
                </div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-icon" style="--accent: var(--warning); --accent-tint: var(--bg-tag-warning)">
                  <el-icon><DataLine /></el-icon>
                </div>
                <div class="mini-stat-body">
                  <div class="mini-stat-value is-text" :style="latestResultStyle">{{ latestResultText }}</div>
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
                <span class="image-count">共 {{ images.length }} 张影像</span>
              </div>
              <div class="table-wrap">
                <el-table :data="images" class="image-table">
                  <template #empty>
                    <div class="empty-state">
                      <div class="empty-icon">
                        <el-icon :size="48"><Picture /></el-icon>
                      </div>
                      <p class="empty-title">暂无超声影像</p>
                      <p class="empty-desc">为这位患者上传超声影像，即可开始辅助检测</p>
                      <el-button class="empty-upload-link" type="primary" link :icon="Upload" @click="$router.push(`/patients/${patient.id}/upload`)">上传第一张影像</el-button>
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

                  <el-table-column label="操作" width="244" fixed="right" align="center">
                    <template #default="{ row }">
                      <div class="action-group">
                        <el-button v-if="row.has_result" class="row-main-action" type="primary" plain @click="$router.push(`/results/${row.result_id}`)">查看结果</el-button>
                        <el-button v-else class="row-main-action" type="primary" plain :icon="VideoPlay" @click="handleDetect(row)">开始检测</el-button>
                        <el-button class="row-preview-action" text @click="previewImage(row)">预览</el-button>
                        <el-dropdown v-if="row.has_result" trigger="click" @command="handleImageAction($event, row)">
                          <el-button class="row-more-action" text :icon="MoreFilled" aria-label="更多影像操作" />
                          <template #dropdown>
                            <el-dropdown-menu>
                              <el-dropdown-item command="print" :icon="Printer">打印报告</el-dropdown-item>
                              <el-dropdown-item command="redetect" :icon="RefreshRight" divided>重新检测</el-dropdown-item>
                            </el-dropdown-menu>
                          </template>
                        </el-dropdown>
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
                <div v-for="d in detections" :key="d.id" class="timeline-item">
                  <div class="timeline-node" :class="detectionClass(d.classification)"></div>
                  <div class="timeline-card">
                    <div class="timeline-card-head">
                      <span class="tl-class" :class="detectionClass(d.classification)">{{ d.classification }}</span>
                      <span class="tl-conf">证据分 {{ d.detection_score != null ? d.detection_score.toFixed(3) : '—' }}</span>
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
    <el-dialog v-model="previewVisible" title="影像预览" width="min(700px, 94vw)" append-to-body class="preview-dialog">
      <ImageViewer v-if="previewSrc" :src="previewSrc" :media-type="previewMediaType" />
    </el-dialog>

    <!-- 打印报告 -->
    <ReportPrint v-model="printVisible" :patient="patient" :result="printResult" :image-url="printImageUrl" />
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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
  Back,
  MoreFilled,
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
const hasPrintableResult = computed(() => detections.value.length > 0 || images.value.some((image) => image.has_result && image.result_id))

const latestResultText = computed(() => {
  const d = latestDetection.value
  if (!d) return '—'
  let label = d.classification || '已检测'
  if (d.severity) label += ` · ${d.severity}`
  // 展示模型真实输出「检测证据分」，不再展示由评估集精度表换算的置信度百分比
  if (d.detection_score != null) label += ` · 证据分 ${d.detection_score.toFixed(3)}`
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
  const colors = ['#437b73', '#64876d', '#a18154', '#937478', '#727b91', '#59818b', '#8c7868', '#5f7b83']
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

async function handleImageAction(command, row) {
  if (command === 'print') return printForImage(row)
  if (command !== 'redetect') return
  try {
    await ElMessageBox.confirm('重新检测将覆盖当前结果，确认继续？', '重新检测', {
      confirmButtonText: '重新检测',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  await handleRedetect(row)
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
.page-back-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 36px;
  margin: -8px 0 14px;
  color: var(--text-secondary);
  font-size: 12px;
  text-decoration: none;
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

/* 布局 */
.detail-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 24px;
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
  border-radius: var(--radius-lg);
  padding: 32px 24px 24px;
  text-align: center;
  box-shadow: 0 4px 24px rgba(23, 50, 57, 0.025);
}
.profile-avatar {
  width: 72px;
  height: 72px;
  border-radius: 24px;
  margin: 0 auto 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 28px;
  font-weight: 600;
  font-family: var(--font-display);
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
  background: var(--border-light);
  margin: 24px 0;
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
  align-items: flex-start;
  gap: 12px;
  font-size: 12px;
  line-height: 1.8;
}
.meta-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-weight: 500;
  flex-shrink: 0;
}
.meta-label .el-icon {
  font-size: 14px;
}
.meta-value {
  font-weight: 500;
  color: var(--text-primary);
  text-align: right;
  min-width: 0;
  overflow-wrap: anywhere;
}

/* 右侧主内容 */
.detail-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 22px;
}

/* 迷你统计 */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1.5fr;
  gap: 14px;
}
.mini-stat {
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 22px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.mini-stat:hover {
  border-color: var(--border-strong);
}
.mini-stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  /* 半透明底色 + 实色图标；不能对容器用 opacity，否则图标会一起变透明 */
  background: var(--accent-tint, var(--bg-hover));
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mini-stat-icon .el-icon {
  color: inherit;
  font-size: 20px;
}
.mini-stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
/* 「最新结果」是一句话而不是一个数字：按正文尺寸排版，避免 20px 大字撑破卡片 */
.mini-stat-value.is-text {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  white-space: normal;
  overflow-wrap: anywhere;
}
.mini-stat-body {
  min-width: 0;
}
.mini-stat-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 5px;
}

/* 数据卡片 */
.data-card {
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 24px rgba(23, 50, 57, 0.025);
  overflow: hidden;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 22px 24px;
  border-bottom: 1px solid var(--border-light);
}
.card-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.card-icon {
  width: 34px;
  height: 34px;
  border-radius: 11px;
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
.image-count { font-size: 12px; color: var(--text-muted); }

/* 表格 */
.table-wrap {
  min-width: 0;
  padding: 0;
  overflow-x: auto;
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
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
}
.action-group .el-button { height: 40px; margin-left: 0; font-size: 12px; }
.row-main-action { min-width: 98px; padding: 0 10px; }
.row-preview-action { padding: 0 10px; color: var(--text-secondary); }
.row-more-action { width: 34px; padding: 0; color: var(--text-secondary); }
.empty-upload-link { min-height: 40px; margin-top: 12px; }

/* 空状态 */
.empty-state {
  padding: 64px 20px;
  text-align: center;
}
.empty-icon {
  width: 72px;
  height: 72px;
  border: 1px solid var(--border-color);
  border-radius: 24px;
  background: var(--bg-page);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  margin-bottom: 20px;
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
  padding: 24px;
  display: flex;
  flex-direction: column;
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
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 18px;
  margin-bottom: 16px;
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

@media (max-width: 640px) {
  .card-header { padding: 18px; }
  .timeline-body { padding: 18px 12px; }
  .tl-time { width: 100%; margin-left: 0; }
  .page-header-actions { width: 100%; margin-left: 0; }
  .page-header-actions .el-button { flex: 1 1 150px; }
}
</style>
