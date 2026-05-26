<template>
  <AppLayout>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <h1 class="page-title">患者管理</h1>
        <p class="page-desc">管理患者信息、查看检测记录与诊断结果</p>
      </div>
      <div class="page-header-meta">
        <span class="meta-badge">
          <el-icon><Calendar /></el-icon>
          {{ today }}
        </span>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card" v-for="(stat, idx) in statItems" :key="idx">
        <div class="stat-card-inner">
          <div class="stat-icon-wrap" :style="{ '--accent': stat.color }">
            <el-icon :size="22"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
        <div class="stat-accent-bar" :style="{ background: stat.color }"></div>
      </div>
    </div>

    <!-- 数据卡片 -->
    <div class="data-card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="toolbar-search">
          <el-icon class="search-icon"><Search /></el-icon>
          <el-input
            v-model="search"
            placeholder="搜索患者姓名、病历号或ID..."
            clearable
            @keyup.enter="handleSearch"
          />
        </div>
        <div class="toolbar-actions">
          <el-button class="btn-ghost" :icon="Download" @click="handleExport">
            导出
          </el-button>
          <el-button type="primary" :icon="Plus" @click="openCreate">
            新增患者
          </el-button>
        </div>
      </div>

      <!-- 表格 -->
      <div class="table-wrap">
        <el-table :data="tableData" v-loading="tableLoading" class="patient-table">
          <template #empty>
            <div class="empty-state">
              <div class="empty-icon">
                <el-icon :size="48"><User /></el-icon>
              </div>
              <p class="empty-title">暂无患者数据</p>
              <p class="empty-desc">点击右上角按钮添加第一位患者</p>
              <el-button type="primary" :icon="Plus" @click="openCreate">
                新增患者
              </el-button>
            </div>
          </template>

          <el-table-column type="index" width="56" align="center">
            <template #header>
              <span class="col-header">#</span>
            </template>
            <template #default="{ $index }">
              <span class="row-index">{{ (page - 1) * size + $index + 1 }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="name" label="患者信息" min-width="160">
            <template #default="{ row }">
              <div class="patient-info">
                <div class="patient-avatar" :style="{ background: stringToColor(row.name) }">
                  {{ row.name ? row.name.charAt(0) : '?' }}
                </div>
                <div class="patient-meta">
                  <div class="patient-name">{{ row.name }}</div>
                  <div class="patient-id">ID: {{ row.id }}</div>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="gender" label="性别" width="80" align="center">
            <template #default="{ row }">
              <span class="gender-tag" :class="row.gender === '男' ? 'gender-male' : 'gender-female'">
                {{ row.gender }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="年龄" width="90" align="center">
            <template #default="{ row }">
              <span class="age-value">{{ row.age }} <small>个月</small></span>
            </template>
          </el-table-column>

          <el-table-column prop="medical_record_no" label="病历号" min-width="140">
            <template #default="{ row }">
              <span class="record-no">{{ row.medical_record_no || '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="最近检测" width="160">
            <template #default="{ row }">
              <div class="detect-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatDateTime(row.last_detect) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="130" align="center">
            <template #default="{ row }">
              <span class="status-pill" :class="statusClass(row)">
                <span class="status-dot"></span>
                {{ statusText(row) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="150" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-group">
                <el-tooltip content="查看详情" placement="top">
                  <button class="icon-btn" @click="handleDetail(row.id)">
                    <el-icon><View /></el-icon>
                  </button>
                </el-tooltip>
                <el-tooltip content="编辑" placement="top">
                  <button class="icon-btn" @click="openEdit(row)">
                    <el-icon><Edit /></el-icon>
                  </button>
                </el-tooltip>
                <el-tooltip content="删除" placement="top">
                  <el-popconfirm
                    title="确定删除该患者吗？"
                    confirm-button-text="删除"
                    cancel-button-text="取消"
                    @confirm="handleDelete(row.id)"
                  >
                    <template #reference>
                      <button class="icon-btn danger">
                        <el-icon><Delete /></el-icon>
                      </button>
                    </template>
                  </el-popconfirm>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-bar" v-if="total > 0">
        <div class="pagination-info">
          共 <strong>{{ total }}</strong> 条记录
        </div>
        <el-pagination
          v-model:current-page="page"
          :page-size="size"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑患者' : '新增患者'"
      width="520px"
      :close-on-click-modal="false"
      append-to-body
      class="patient-dialog"
    >
      <div class="dialog-body">
        <el-form ref="dialogFormRef" :model="dialogForm" :rules="dialogRules" label-width="90px">
          <el-form-item label="姓名" prop="name">
            <el-input v-model="dialogForm.name" placeholder="请输入患者姓名" />
          </el-form-item>
          <el-form-item label="性别" prop="gender">
            <el-select v-model="dialogForm.gender" placeholder="请选择性别" style="width: 100%">
              <el-option label="男" value="男" />
              <el-option label="女" value="女" />
            </el-select>
          </el-form-item>
          <el-form-item label="年龄(月)" prop="age">
            <el-input-number v-model="dialogForm.age" :min="0" :max="144" style="width: 100%" placeholder="请输入月龄" />
          </el-form-item>
          <el-form-item label="病历号" prop="medical_record_no">
            <el-input v-model="dialogForm.medical_record_no" placeholder="请输入病历号" />
          </el-form-item>
          <el-form-item label="临床症状" prop="clinical_symptoms">
            <el-input
              v-model="dialogForm.clinical_symptoms"
              type="textarea"
              :rows="3"
              placeholder="请描述临床症状..."
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
            {{ editingId ? '保存修改' : '确认新增' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Download,
  Search,
  User,
  UserFilled,
  Bell,
  Warning,
  Calendar,
  Clock,
  View,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import { getPatients, getPatientStats, createPatient, updatePatient, deletePatient } from '../api/patients'

const router = useRouter()

const search = ref('')
const tableData = ref([])
const tableLoading = ref(false)
const page = ref(1)
const size = ref(10)
const total = ref(0)

const stats = ref({
  total_patients: 0,
  today_new: 0,
  pending: 0,
  positive: 0,
})

const statItems = computed(() => [
  {
    label: '总患者数',
    value: stats.value.total_patients ?? 0,
    icon: UserFilled,
    color: 'var(--primary)',
  },
  {
    label: '今日新增',
    value: stats.value.today_new ?? 0,
    icon: Plus,
    color: 'var(--success)',
  },
  {
    label: '待检测',
    value: stats.value.pending ?? 0,
    icon: Bell,
    color: 'var(--warning)',
  },
  {
    label: '阳性病例',
    value: stats.value.positive ?? 0,
    icon: Warning,
    color: 'var(--danger)',
  },
])

const today = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const dialogVisible = ref(false)
const editingId = ref(null)
const submitLoading = ref(false)
const dialogFormRef = ref(null)

const dialogForm = reactive({
  name: '',
  gender: '',
  age: null,
  medical_record_no: '',
  clinical_symptoms: '',
})

const dialogRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  age: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
}

function stringToColor(str) {
  if (!str) return 'var(--text-muted)'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = [
    '#2563eb', '#059669', '#d97706', '#dc2626',
    '#7c3aed', '#0891b2', '#be185d', '#4338ca',
  ]
  return colors[Math.abs(hash) % colors.length]
}

function statusClass(row) {
  const s = row.status || ''
  if (s.startsWith('positive')) return 'status-danger'
  if (s === 'negative') return 'status-success'
  if (s === 'poor_quality') return 'status-warning'
  return 'status-default'
}

function statusText(row) {
  const s = row.status || ''
  if (s.startsWith('positive:')) {
    const sev = s.split(':')[1]
    return sev ? `阳性 ${sev}` : '阳性'
  }
  if (s === 'negative') return '阴性'
  if (s === 'poor_quality') return '图像不佳'
  return '未检测'
}

function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

function resetDialogForm() {
  dialogForm.name = ''
  dialogForm.gender = ''
  dialogForm.age = null
  dialogForm.medical_record_no = ''
  dialogForm.clinical_symptoms = ''
}

async function fetchData() {
  tableLoading.value = true
  try {
    const res = await getPatients({ search: search.value, page: page.value, size: size.value })
    tableData.value = res.data.items ?? res.data.data ?? res.data
    total.value = res.data.total ?? 0
  } finally {
    tableLoading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await getPatientStats()
    stats.value = res.data
  } catch {
    // ignore
  }
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function openCreate() {
  editingId.value = null
  resetDialogForm()
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  dialogForm.name = row.name
  dialogForm.gender = row.gender
  dialogForm.age = row.age
  dialogForm.medical_record_no = row.medical_record_no ?? ''
  dialogForm.clinical_symptoms = row.clinical_symptoms ?? ''
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await dialogFormRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (editingId.value) {
      await updatePatient(editingId.value, { ...dialogForm })
      ElMessage.success('编辑成功')
    } else {
      await createPatient({ ...dialogForm })
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    fetchData()
    fetchStats()
  } catch {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(id) {
  try {
    await deletePatient(id)
    ElMessage.success('删除成功')
    fetchData()
    fetchStats()
  } catch {
    ElMessage.error('删除失败')
  }
}

function handleDetail(id) {
  router.push(`/patients/${id}`)
}

function handleExport() {
  ElMessage.info('导出功能开发中')
}

onMounted(() => {
  fetchData()
  fetchStats()
})
</script>

<style scoped>
/* ========== 页面头部 ========== */
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
.page-header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}
.meta-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  font-weight: 500;
}
.meta-badge .el-icon {
  color: var(--primary);
}

/* ========== 统计卡片 ========== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}
.stat-card-inner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 20px;
}
.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  opacity: 0.1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  flex-shrink: 0;
  transition: opacity 0.2s ease;
}
.stat-card:hover .stat-icon-wrap {
  opacity: 0.15;
}
.stat-icon-wrap .el-icon {
  color: var(--accent);
  opacity: 1;
}
.stat-body {
  flex: 1;
}
.stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
  font-weight: 500;
}
.stat-accent-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  opacity: 0.8;
}

/* ========== 数据卡片 ========== */
.data-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
}
.toolbar-search {
  position: relative;
  width: 320px;
}
.toolbar-search .search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 16px;
  z-index: 1;
  pointer-events: none;
}
.toolbar-search :deep(.el-input__wrapper) {
  padding-left: 36px !important;
}
.toolbar-actions {
  display: flex;
  gap: 8px;
}
.btn-ghost {
  background: transparent !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border-color) !important;
  font-weight: 500 !important;
}
.btn-ghost:hover {
  border-color: var(--text-muted) !important;
  color: var(--text-primary) !important;
  background: var(--bg-hover) !important;
}

/* 表格包裹 */
.table-wrap {
  padding: 0 4px;
}

/* 表格样式 */
.patient-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: var(--bg-page) !important;
  color: var(--text-secondary) !important;
  font-weight: 600 !important;
  font-size: 12px;
  text-transform: none;
  letter-spacing: 0;
  border-bottom: 1px solid var(--border-color);
  padding: 12px 0;
}
.patient-table :deep(.el-table__row) {
  transition: background 0.15s ease;
}
.patient-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: var(--bg-hover) !important;
}
.patient-table :deep(td.el-table__cell) {
  padding: 14px 0;
  border-bottom: 1px solid var(--border-light);
}

/* 列头 */
.col-header {
  font-weight: 600;
  color: var(--text-muted);
}

/* 行号 */
.row-index {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-display);
  font-weight: 500;
}

/* 患者信息 */
.patient-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.patient-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
  text-shadow: 0 1px 2px rgba(0,0,0,0.15);
}
.patient-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.patient-id {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
  font-family: var(--font-display);
}

/* 性别标签 */
.gender-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}
.gender-male {
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
}
.gender-female {
  background: rgba(219, 39, 119, 0.08);
  color: #db2777;
}

/* 年龄 */
.age-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.age-value small {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 400;
}

/* 病历号 */
.record-no {
  font-family: var(--font-display);
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  letter-spacing: 0.02em;
}

/* 检测时间 */
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
.status-danger {
  background: var(--bg-tag-danger);
  color: var(--danger);
}
.status-danger .status-dot {
  background: var(--danger);
}
.status-warning {
  background: var(--bg-tag-warning);
  color: var(--warning);
}
.status-warning .status-dot {
  background: var(--warning);
}
.status-default {
  background: var(--bg-tag-info);
  color: var(--primary);
}
.status-default .status-dot {
  background: var(--primary);
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
.icon-btn.danger:hover {
  background: var(--bg-tag-danger);
  color: var(--danger);
}

/* ========== 分页 ========== */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-page);
}
.pagination-info {
  font-size: 12px;
  color: var(--text-muted);
}
.pagination-info strong {
  color: var(--text-primary);
  font-weight: 600;
}

/* ========== 空状态 ========== */
.empty-state {
  padding: 60px 0;
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
  margin: 0 0 20px;
}

/* ========== 弹窗 ========== */
.patient-dialog :deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-color);
  font-weight: 700;
  font-size: 16px;
}
.patient-dialog :deep(.el-dialog__body) {
  padding: 0;
}
.dialog-body {
  padding: 24px;
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
}

/* ========== 响应式 ========== */
@media (max-width: 1100px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 12px; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .toolbar-search { width: 100%; }
  .toolbar-actions { justify-content: flex-end; }
  .stats-row { grid-template-columns: 1fr; }
  .pagination-bar { flex-direction: column; gap: 12px; }
}
</style>
