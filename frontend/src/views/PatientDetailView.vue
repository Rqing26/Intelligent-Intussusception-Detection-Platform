<template>
  <AppLayout>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <h1 class="page-title">患者详情</h1>
        <p class="page-desc">查看患者信息、超声影像及检测结果</p>
      </div>
      <div class="page-header-actions">
        <el-button type="primary" @click="printVisible = true" v-if="patient">
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
                <div class="meta-row">
                  <span class="meta-label"><el-icon><FirstAidKit /></el-icon>临床诊断</span>
                  <span class="meta-value">{{ patient.clinical_symptoms || '—' }}</span>
                </div>
                <div class="meta-row">
                  <span class="meta-label"><el-icon><Clock /></el-icon>录入时间</span>
                  <span class="meta-value">{{ patient.created_at }}</span>
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
                        <span>{{ row.uploaded_at }}</span>
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
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 影像预览 -->
    <el-dialog v-model="previewVisible" title="影像预览" width="700px" append-to-body class="preview-dialog">
      <ImageViewer v-if="previewSrc" :src="previewSrc" />
    </el-dialog>

    <!-- 打印报告 -->
    <ReportPrint v-model="printVisible" :patient="patient" :result="printResult" :image-url="printImageUrl" />
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
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
} from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import ImageViewer from '../components/ImageViewer.vue'
import ReportPrint from '../components/ReportPrint.vue'
import { getPatient } from '../api/patients'
import { getImageInfo, getImageUrl, runDetection } from '../api/images'
import { getResult } from '../api/results'

const route = useRoute()
const loading = ref(false)
const patient = ref(null)
const images = ref([])
const previewVisible = ref(false)
const previewSrc = ref('')
const printVisible = ref(false)
const printResult = ref(null)
const printImageUrl = ref('')

const latestResultText = computed(() => {
  const detected = images.value.filter((i) => i.has_result)
  if (detected.length === 0) return '—'
  return '已检测'
})

const latestResultStyle = computed(() => {
  const detected = images.value.filter((i) => i.has_result)
  if (detected.length === 0) return {}
  return { color: 'var(--success)' }
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
            return { ...img, has_result: infoRes.data.has_result, result_id: infoRes.data.result_id }
          } catch {
            return { ...img, has_result: false, result_id: null }
          }
        })
      )
    }
  } catch {
    ElMessage.error('获取患者信息失败')
  } finally {
    loading.value = false
  }
}

function previewImage(row) {
  previewSrc.value = getImageUrl(row.id)
  previewVisible.value = true
}

async function handleDetect(row) {
  try {
    const res = await runDetection(row.id)
    const resultId = res.data.id ?? res.data.result_id
    if (resultId) {
      ElMessage.success('检测完成')
      const router = (await import('vue-router')).useRouter()
      router.push(`/results/${resultId}`)
    }
  } catch {
    ElMessage.error('检测失败')
  }
}

async function printForImage(row) {
  try {
    const res = await getResult(row.result_id)
    printResult.value = res.data
    printImageUrl.value = getImageUrl(row.id)
    printVisible.value = true
  } catch {
    ElMessage.error('获取检测结果失败')
  }
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
</style>
