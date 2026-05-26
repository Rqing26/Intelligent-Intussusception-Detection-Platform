<template>
  <AppLayout>
    <div class="page-header-row">
      <div>
        <h2 class="page-title">患者管理</h2>
        <div class="breadcrumb">首页 / 患者管理</div>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div>
          <div class="stat-value">{{ stats.total_patients }}</div>
          <div class="stat-label">总患者数</div>
        </div>
        <div class="stat-icon">👤</div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-value">{{ stats.today_new }}</div>
          <div class="stat-label">今日新增</div>
        </div>
        <div class="stat-icon">+</div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-label">待检测</div>
        </div>
        <div class="stat-icon">!</div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-value">{{ stats.positive }}</div>
          <div class="stat-label">阳性病例</div>
        </div>
        <div class="stat-icon">⚠</div>
      </div>
    </div>

    <div class="card">
      <div class="toolbar">
        <el-input
          v-model="search"
          placeholder="搜索患者姓名、病历号或ID..."
          clearable
          style="width: 320px"
          @keyup.enter="handleSearch"
        />
        <div class="toolbar-actions">
          <el-button class="btn-secondary" @click="handleExport">导出数据</el-button>
          <el-button type="primary" :icon="Plus" @click="openCreate">+ 新增患者</el-button>
        </div>
      </div>

      <el-table :data="tableData" v-loading="tableLoading" style="width: 100%">
        <template #empty>
          <div class="empty-state">
            <p>暂无患者数据</p>
            <el-button type="primary" @click="openCreate">新增第一位患者</el-button>
          </div>
        </template>
        <el-table-column prop="id" label="ID" width="70">
          <template #default="{ row }">
            <strong style="font-family: var(--font-display)">#{{ row.id }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="姓名" width="110" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column label="年龄" width="90">
          <template #default="{ row }">{{ row.age }} 个月</template>
        </el-table-column>
        <el-table-column prop="medical_record_no" label="病历号" min-width="150" />
        <el-table-column label="最近检测" width="160">
          <template #default="{ row }">{{ formatDateTime(row.last_detect) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="140">
          <template #default="{ row }">
            <span :class="['seal-tag', statusClass(row)]">{{ statusText(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <div class="action-group">
              <span class="action-btn" @click="handleDetail(row.id)">详情</span>
              <span class="action-btn" @click="openEdit(row)">编辑</span>
              <el-popconfirm title="确定删除该患者吗？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <span class="action-btn danger">删除</span>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="page"
          :page-size="size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑患者' : '新增患者'"
      width="520px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form ref="dialogFormRef" :model="dialogForm" :rules="dialogRules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="dialogForm.name" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="dialogForm.gender" style="width: 100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄(月)" prop="age">
          <el-input-number v-model="dialogForm.age" :min="0" :max="144" style="width: 100%" />
        </el-form-item>
        <el-form-item label="病历号" prop="medical_record_no">
          <el-input v-model="dialogForm.medical_record_no" />
        </el-form-item>
        <el-form-item label="临床症状" prop="clinical_symptoms">
          <el-input v-model="dialogForm.clinical_symptoms" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
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

function statusClass(row) {
  const s = row.status || ''
  if (s.startsWith('positive')) return 'seal-vermillion'
  if (s === 'negative') return 'seal-malachite'
  if (s === 'poor_quality') return 'seal-gold'
  return 'seal-ink'
}

function statusText(row) {
  const s = row.status || ''
  if (s.startsWith('positive:')) {
    const sev = s.split(':')[1]
    return sev ? `阳性：${sev}` : '阳性'
  }
  if (s === 'negative') return '阴性'
  if (s === 'poor_quality') return '图像质量不佳'
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

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: var(--bg-stat-card);
  border: 1px solid var(--border-color);
  padding: 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
  transition: all 0.2s;
}
.stat-card:hover {
  border-color: var(--gold-dim);
  box-shadow: var(--shadow-sm);
}
.stat-card::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 20px;
  right: 20px;
  height: 2px;
  background: var(--gold);
}
.stat-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--lapis-deep, var(--text-primary));
  line-height: 1.1;
}
.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
}
.stat-icon {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--text-muted);
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
  left: 24px;
  width: 48px;
  height: 2px;
  background: var(--primary);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  gap: 12px;
}
.toolbar-actions {
  display: flex;
  gap: 8px;
}
.btn-secondary {
  background: transparent !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border-color) !important;
}
.btn-secondary:hover {
  border-color: var(--text-muted) !important;
  color: var(--text-primary) !important;
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
.seal-vermillion { background: var(--bg-tag-danger); color: var(--danger); border-color: rgba(139, 38, 53, 0.3); }
.seal-malachite { background: var(--bg-tag-success); color: var(--success); border-color: rgba(45, 90, 63, 0.3); }
.seal-gold { background: var(--bg-tag-warning); color: var(--warning); border-color: rgba(166, 93, 58, 0.3); }
.seal-ink { background: rgba(44, 36, 27, 0.06); color: var(--text-secondary); border-color: rgba(44, 36, 27, 0.2); }

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
.action-btn.danger {
  color: var(--danger);
}
.action-btn.danger:hover {
  border-color: var(--danger);
  background: rgba(139, 38, 53, 0.04);
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
}

.empty-state {
  padding: 60px 0;
  color: var(--text-muted);
  text-align: center;
}

@media (max-width: 1100px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}
</style>
