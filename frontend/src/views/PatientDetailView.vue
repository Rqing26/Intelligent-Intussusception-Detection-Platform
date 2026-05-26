<template>
  <AppLayout>
    <div class="page-header-row">
      <div>
        <h2 class="page-title">患者详情</h2>
        <div class="breadcrumb">首页 / 患者管理 / {{ patient?.name || '...' }}</div>
      </div>
      <el-button type="primary" @click="printVisible = true" v-if="patient">
        <el-icon><Printer /></el-icon>打印报告
      </el-button>
    </div>

    <div v-loading="loading">
      <template v-if="patient">
        <div class="patient-profile">
          <div class="profile-card">
            <div class="profile-avatar">{{ patient.name?.charAt(0) }}</div>
            <div class="profile-name">{{ patient.name }}</div>
            <div class="profile-id">病历号 {{ patient.medical_record_no }}</div>
            <div class="profile-meta">
              <div class="profile-meta-row">
                <span class="label">性别</span>
                <span class="value">{{ patient.gender }}</span>
              </div>
              <div class="profile-meta-row">
                <span class="label">年龄</span>
                <span class="value">{{ patient.age }} 个月</span>
              </div>
              <div class="profile-meta-row">
                <span class="label">临床诊断</span>
                <span class="value">{{ patient.clinical_symptoms || '—' }}</span>
              </div>
              <div class="profile-meta-row">
                <span class="label">录入时间</span>
                <span class="value">{{ patient.created_at }}</span>
              </div>
            </div>
            <div class="profile-actions">
              <button class="btn-main" @click="$router.push(`/patients/${patient.id}/upload`)">上传影像</button>
              <button class="btn-sub">编辑信息</button>
            </div>
          </div>

          <div class="detail-main">
            <div class="detail-grid">
              <div class="detail-item">
                <div class="label">影像数量</div>
                <div class="value">{{ images.length }} 张</div>
              </div>
              <div class="detail-item">
                <div class="label">检测次数</div>
                <div class="value">{{ images.filter(i => i.has_result).length }} 次</div>
              </div>
              <div class="detail-item">
                <div class="label">最新结果</div>
                <div class="value" :style="latestResultStyle">{{ latestResultText }}</div>
              </div>
            </div>

            <div class="card">
              <div class="card-header">
                <h3>超声影像列表</h3>
                <el-button type="primary" @click="$router.push(`/patients/${patient.id}/upload`)">+ 上传新影像</el-button>
              </div>
              <div class="card-body">
                <el-table :data="images" style="width: 100%">
                  <template #empty>
                    <div class="empty-state">暂无超声影像数据</div>
                  </template>
                  <el-table-column prop="id" label="ID" width="60" />
                  <el-table-column prop="filename" label="文件名" min-width="180" />
                  <el-table-column label="上传时间" width="170">
                    <template #default="{ row }">{{ row.uploaded_at }}</template>
                  </el-table-column>
                  <el-table-column label="状态" width="100">
                    <template #default="{ row }">
                      <span :class="['seal-tag', row.has_result ? 'seal-malachite' : 'seal-gold']">
                        {{ row.has_result ? '已检测' : '待检测' }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="240" fixed="right">
                    <template #default="{ row }">
                      <div class="action-group">
                        <span class="action-btn" @click="previewImage(row)">预览</span>
                        <span v-if="!row.has_result" class="action-btn warn" @click="handleDetect(row)">检测</span>
                        <span v-if="row.has_result" class="action-btn" @click="$router.push(`/results/${row.result_id}`)">查看结果</span>
                        <span v-if="row.has_result" class="action-btn" @click="printForImage(row)">打印</span>
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

    <el-dialog v-model="previewVisible" title="影像预览" width="700px" append-to-body>
      <ImageViewer v-if="previewSrc" :src="previewSrc" />
    </el-dialog>

    <ReportPrint
      v-model="printVisible"
      :patient="patient"
      :result="printResult"
      :image-url="printImageUrl"
    />
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
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
  const detected = images.value.filter(i => i.has_result)
  if (detected.length === 0) return '—'
  return '已检测'
})

const latestResultStyle = computed(() => {
  const detected = images.value.filter(i => i.has_result)
  if (detected.length === 0) return {}
  return { color: 'var(--success)' }
})

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
      ;(await import('vue-router')).useRouter().push(`/results/${resultId}`)
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

.patient-profile {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
}
.profile-card {
  background: var(--bg-profile);
  border: 1px solid var(--border-color);
  padding: 28px 20px;
  text-align: center;
  position: relative;
  height: fit-content;
}
.profile-card::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 2px;
  background: var(--gold);
}
.profile-avatar {
  width: 72px;
  height: 72px;
  margin: 0 auto 16px;
  border: 2px solid var(--gold-dim);
  border-radius: 50%;
  background: var(--primary);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  font-family: var(--font-display);
}
.profile-name {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
  color: var(--text-primary);
}
.profile-id {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
  margin-bottom: 20px;
}
.profile-meta {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
}
.profile-meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}
.profile-meta-row:last-child {
  border-bottom: none;
}
.profile-meta-row .label {
  color: var(--text-muted);
}
.profile-meta-row .value {
  font-weight: 700;
  color: var(--text-primary);
}
.profile-actions {
  display: flex;
  gap: 8px;
  margin-top: 20px;
}
.profile-actions button {
  flex: 1;
  padding: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  border: none;
  font-family: var(--font-sans);
}
.btn-main {
  background: var(--primary);
  color: var(--text-inverse);
}
.btn-sub {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color) !important;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.detail-item {
  background: var(--bg-detail-item);
  border: 1px solid var(--border-color);
  padding: 16px;
  position: relative;
}
.detail-item::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 16px;
  width: 32px;
  height: 2px;
  background: var(--primary);
}
.detail-item .label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 6px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-family: var(--font-display);
}
.detail-item .value {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color);
}
.card-header h3 {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.06em;
  margin: 0;
}

.seal-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  border: 1px solid;
}
.seal-malachite {
  background: var(--bg-tag-success);
  color: var(--success);
  border-color: rgba(45, 90, 63, 0.3);
}
.seal-gold {
  background: var(--bg-tag-warning);
  color: var(--warning);
  border-color: rgba(166, 93, 58, 0.3);
}

.action-group {
  display: flex;
  gap: 4px;
}
.action-btn {
  padding: 4px 10px;
  font-size: 12px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--primary);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.2s;
  border-radius: var(--radius-sm);
}
.action-btn:hover {
  border-color: var(--primary);
  background: rgba(30, 58, 95, 0.04);
}
.action-btn.warn {
  color: var(--warning);
}
.action-btn.warn:hover {
  border-color: var(--warning);
  background: rgba(166, 93, 58, 0.04);
}

.empty-state {
  padding: 50px 0;
  color: var(--text-muted);
  text-align: center;
}

@media (max-width: 1100px) {
  .patient-profile {
    grid-template-columns: 1fr;
  }
  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
