<template>
  <AppLayout>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <span class="page-eyebrow">PATIENT WORKSPACE</span>
        <h1 class="page-title">患者管理</h1>
        <p class="page-desc">让每一份档案清晰有序，让每一次诊疗有据可循。</p>
      </div>
      <div class="page-header-meta">
        <span class="meta-badge">
          <el-icon><Calendar /></el-icon>
          {{ today }}
        </span>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增患者</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card" :class="{ 'stat-card-primary': idx === 0 }" v-for="(stat, idx) in statItems" :key="idx">
        <div class="stat-card-inner">
          <div class="stat-body">
            <div class="stat-label">{{ stat.label }}</div>
            <div class="stat-value">{{ stat.value }}<span>位</span></div>
            <div class="stat-caption">{{ stat.description }}</div>
          </div>
          <!-- 用「半透明底色 + 实色图标」表达强调色，不能对容器用 opacity（会把图标一起变透明） -->
          <div
            class="stat-icon-wrap"
            :style="{ '--accent': stat.color, '--accent-tint': `var(${stat.tint})` }"
          >
            <el-icon :size="20"><component :is="stat.icon" /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据卡片 -->
    <div class="data-card">
      <div class="data-card-heading">
        <div><h2>患者档案 <span>{{ total }}</span></h2><p>集中管理患者资料与最近一次检测情况</p></div>
        <div class="toolbar-actions">
          <el-button class="btn-ghost" :icon="Download" :loading="exporting" @click="handleExport">导出档案</el-button>
        </div>
      </div>
      <!-- 工具栏 -->
      <div class="toolbar">
        <div class="search-controls">
        <div class="toolbar-search">
          <el-icon class="search-icon"><Search /></el-icon>
          <el-input
            v-model="search"
            placeholder="搜索姓名、病历号或 ID"
            aria-label="搜索患者"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          />
        </div>
          <div class="filter-actions">
            <el-button type="primary" :icon="Search" :loading="tableLoading" @click="handleSearch">查询</el-button>
            <el-button :disabled="!search" @click="resetSearch">重置</el-button>
          </div>
        </div>
        <el-button class="refresh-button" text :icon="Refresh" :disabled="tableLoading" @click="handleRefresh">刷新列表</el-button>
      </div>

      <!-- 表格 -->
      <div class="table-wrap">
        <div v-if="loadError" class="empty-state" role="alert">
          <div class="empty-icon"><el-icon :size="30"><Warning /></el-icon></div>
          <p class="empty-title">暂时无法加载患者档案</p>
          <p class="empty-desc">请检查网络连接后重试</p>
          <el-button :icon="Refresh" @click="handleRefresh">重新加载</el-button>
        </div>
        <template v-else-if="tableLoading && !tableData.length">
          <el-skeleton :rows="6" animated class="list-skeleton" />
        </template>
        <el-table v-else :data="tableData" v-loading="tableLoading" class="patient-table">
          <template #empty>
            <div class="empty-state">
              <div class="empty-icon">
                <el-icon :size="48"><User /></el-icon>
              </div>
              <p class="empty-title">{{ search ? '未找到匹配的患者' : '从第一份患者档案开始' }}</p>
              <p class="empty-desc">{{ search ? '尝试其他姓名、病历号或 ID' : '建立档案后，即可上传影像并开展辅助诊断' }}</p>
              <el-button v-if="search" @click="resetSearch">清空搜索</el-button>
              <el-button v-else type="primary" :icon="Plus" @click="openCreate">
                新增患者
              </el-button>
            </div>
          </template>

          <el-table-column type="index" width="44" align="center">
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
                  {{ avatarText(row.name) }}
                </div>
                <div class="patient-meta">
                  <button class="patient-name" @click="handleDetail(row.id)">{{ row.name }}</button>
                  <div class="patient-id">ID: {{ row.id }}</div>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="性别 / 月龄" width="96" align="center">
            <template #default="{ row }">
              <span class="gender-tag" :class="genderClass(row.gender)">
                {{ genderText(row.gender) }}
              </span>
              <span class="age-value"> · {{ row.age }} <small>个月</small></span>
            </template>
          </el-table-column>

          <el-table-column prop="medical_record_no" label="病历号" min-width="128">
            <template #default="{ row }">
              <span class="record-no">{{ row.medical_record_no || '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="最近检测" width="150">
            <template #default="{ row }">
              <div class="detect-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatDateTime(row.last_detect) }}</span>
              </div>
              <div class="detect-count">{{ row.detect_count ? `累计检测 ${row.detect_count} 次` : '尚无检测记录' }}</div>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="106" align="center">
            <template #default="{ row }">
              <span class="status-pill" :class="statusClass(row)">
                <span class="status-dot"></span>
                {{ statusText(row) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="患者操作" :width="isCompactTable ? 160 : 222" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-group">
                <button class="row-upload" :aria-label="`为${row.name}上传检测`" @click="router.push(`/patients/${row.id}/upload`)"><el-icon><Upload /></el-icon>上传检测</button>
                <button class="row-detail" @click="handleDetail(row.id)">查看档案</button>
                <el-dropdown trigger="click" placement="bottom-end" @command="handlePatientCommand($event, row)">
                  <button class="row-more" :aria-label="`${row.name}的更多操作`" title="更多操作"><el-icon><MoreFilled /></el-icon></button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-if="isCompactTable" command="detail" :icon="View">查看档案</el-dropdown-item>
                      <el-dropdown-item command="edit" :icon="Edit">编辑资料</el-dropdown-item>
                      <el-dropdown-item command="delete" :icon="Delete" divided class="danger-menu-item">删除患者</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
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
          :pager-count="5"
          layout="prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </div>
    <div class="list-footnote"><el-icon><InfoFilled /></el-icon><span>检测结果仅供临床参考，请结合病史、体征及其他检查综合判断。</span></div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑患者' : '新增患者'"
      width="min(560px, calc(100vw - 32px))"
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
          <el-form-item label="住院号" prop="hospital_no">
            <el-input v-model="dialogForm.hospital_no" placeholder="请输入住院号" />
          </el-form-item>
          <el-form-item label="检查部位" prop="exam_part">
            <el-select v-model="dialogForm.exam_part" placeholder="请选择检查部位" clearable style="width: 100%">
              <el-option label="腹部" value="腹部" />
              <el-option label="急腹症" value="急腹症" />
              <el-option label="腹部+盆腔" value="腹部+盆腔" />
            </el-select>
          </el-form-item>
          <el-form-item label="出生日期" prop="birth_date">
            <el-date-picker v-model="dialogForm.birth_date" type="date" value-format="YYYY-MM-DD" placeholder="选择出生日期，自动推算月龄" style="width: 100%" @change="autoFillAgeFromBirth" />
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
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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
  Refresh,
  InfoFilled,
  Upload,
  MoreFilled,
} from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import { getPatients, getPatientStats, createPatient, updatePatient, deletePatient, exportPatients } from '../api/patients'
import { formatDateTime } from '../utils/time'

const router = useRouter()

const search = ref('')
const tableData = ref([])
const tableLoading = ref(false)
const loadError = ref(false)
const exporting = ref(false)
const isCompactTable = ref(false)
let tableMediaQuery
function updateTableWidth(event) { isCompactTable.value = event.matches }
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
    description: '已建立的患者档案',
    value: stats.value.total_patients ?? 0,
    icon: UserFilled,
    color: 'var(--primary)',
    tint: '--bg-tag-info',
  },
  {
    label: '今日新增',
    description: '今日录入的新档案',
    value: stats.value.today_new ?? 0,
    icon: Plus,
    color: 'var(--success)',
    tint: '--bg-tag-success',
  },
  {
    label: '待检测',
    description: '等待首次影像检测',
    value: stats.value.pending ?? 0,
    icon: Bell,
    color: 'var(--warning)',
    tint: '--bg-tag-warning',
  },
  {
    label: '阳性病例',
    description: '最近一次检测为阳性',
    value: stats.value.positive ?? 0,
    icon: Warning,
    color: 'var(--danger)',
    tint: '--bg-tag-danger',
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
  hospital_no: '',
  exam_part: '',
  birth_date: '',
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
    '#557c76', '#6a8195', '#948169', '#977a7d',
    '#7f8295', '#61868b', '#8d7990', '#6e846b',
  ]
  return colors[Math.abs(hash) % colors.length]
}

/**
 * 头像文字：姓名首字。
 * 但以数字开头的姓名（现网有 "16"、"15test" 这类）只取首字符会得到一列相同的「1」，
 * 起不到区分作用，所以数字开头的取前两位。
 */
function avatarText(name) {
  const v = String(name ?? '').trim()
  if (!v) return '?'
  if (/^\d/.test(v)) return v.slice(0, 2)
  return v.charAt(0)
}

/**
 * 性别展示：库里可能存中文「男/女」，也可能存英文 male/female。
 * 不认识的取值走中性灰，不能默认落成"女"（原来除了「男」以外全按女样式渲染）。
 */
function genderClass(gender) {
  const v = String(gender ?? '').trim().toLowerCase()
  if (v === '男' || v === 'male' || v === 'm') return 'gender-male'
  if (v === '女' || v === 'female' || v === 'f') return 'gender-female'
  return 'gender-unknown'
}

function genderText(gender) {
  const v = String(gender ?? '').trim()
  if (!v) return '—'
  const low = v.toLowerCase()
  if (low === 'male' || low === 'm') return '男'
  if (low === 'female' || low === 'f') return '女'
  return v
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

function resetDialogForm() {
  dialogForm.name = ''
  dialogForm.gender = ''
  dialogForm.age = null
  dialogForm.medical_record_no = ''
  dialogForm.hospital_no = ''
  dialogForm.exam_part = ''
  dialogForm.birth_date = ''
  dialogForm.clinical_symptoms = ''
}

function autoFillAgeFromBirth(val) {
  if (!val) return
  const bd = new Date(val)
  if (Number.isNaN(bd.getTime())) return
  const now = new Date()
  let months = (now.getFullYear() - bd.getFullYear()) * 12 + (now.getMonth() - bd.getMonth())
  if (now.getDate() < bd.getDate()) months -= 1
  dialogForm.age = Math.max(0, months)
}

async function fetchData() {
  tableLoading.value = true
  loadError.value = false
  try {
    const res = await getPatients({ search: search.value, page: page.value, size: size.value })
    tableData.value = res.data.items ?? res.data.data ?? res.data
    total.value = res.data.total ?? 0
  } catch {
    loadError.value = true
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

function resetSearch() { search.value = ''; handleSearch() }
function handleRefresh() { fetchData(); fetchStats() }

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
  dialogForm.hospital_no = row.hospital_no ?? ''
  dialogForm.exam_part = row.exam_part ?? ''
  dialogForm.birth_date = row.birth_date ?? ''
  dialogForm.clinical_symptoms = row.clinical_symptoms ?? ''
  dialogVisible.value = true
}

async function handleSubmit() {
  if (submitLoading.value) return
  submitLoading.value = true
  try {
    const valid = await dialogFormRef.value.validate().catch(() => false)
    if (!valid) return

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

async function handlePatientCommand(command, row) {
  if (command === 'detail') return handleDetail(row.id)
  if (command === 'edit') return openEdit(row)
  if (command !== 'delete') return
  try {
    await ElMessageBox.confirm(`确定删除“${row.name}”的患者档案吗？此操作无法撤销。`, '删除患者', {
      confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning',
      customClass: 'danger-confirm-dialog',
    })
  } catch { return }
  await handleDelete(row.id)
}

async function handleExport() {
  if (exporting.value) return
  exporting.value = true
  try {
    const res = await exportPatients()
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'patients.csv'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  tableMediaQuery = window.matchMedia('(max-width: 760px)')
  updateTableWidth(tableMediaQuery)
  tableMediaQuery.addEventListener('change', updateTableWidth)
  fetchData()
  fetchStats()
})
onUnmounted(() => tableMediaQuery?.removeEventListener('change', updateTableWidth))
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 28px; }
.page-eyebrow { color: var(--primary); font-size: 9px; font-weight: 600; letter-spacing: 2px; display: block; margin-bottom: 8px; }
.page-title { font-size: 30px; font-weight: 600; letter-spacing: -.7px; margin: 0 0 7px; color: var(--text-primary); line-height: 1.25; }
.page-desc { font-size: 12px; color: var(--text-muted); margin: 0; }
.page-header-meta { display: flex; align-items: center; gap: 15px; }
.page-header-meta .el-button { height: 40px; padding: 0 19px; }
.meta-badge { display: inline-flex; align-items: center; gap: 7px; font-size: 11px; color: var(--text-secondary); }
.meta-badge .el-icon { font-size: 14px; }
.stats-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-bottom: 28px; }
.stat-card { border: 1px solid var(--border-color); border-radius: 16px; background: var(--bg-card); overflow: hidden; position: relative; box-shadow: var(--shadow-sm); }
.stat-card-inner { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 24px 24px 20px; }
.stat-label { color: var(--text-secondary); font-size: 12px; font-weight: 500; margin-bottom: 14px; }
.stat-value { color: var(--text-primary); font-size: 36px; font-weight: 500; line-height: 1.05; letter-spacing: -1px; font-variant-numeric: tabular-nums; }
.stat-value span { color: var(--text-muted); font-size: 10px; margin-left: 7px; letter-spacing: 0; font-weight: 400; }
.stat-caption { color: var(--text-muted); margin-top: 13px; font-size: 10px; }
.stat-icon-wrap { width: 37px; height: 37px; background: var(--accent-tint); color: var(--accent); border-radius: 11px; display: grid; place-items: center; flex-shrink: 0; }
.stat-card-primary { background: var(--bg-sidebar); border-color: var(--bg-sidebar); }
.stat-card-primary::after { content: ''; position: absolute; width: 145px; height: 145px; border: 1px solid #376159; border-radius: 50%; right: -65px; bottom: -70px; pointer-events: none; }
.stat-card-primary .stat-label { color: #bdd3ca; }
.stat-card-primary .stat-value { color: #fff; }
.stat-card-primary .stat-value span, .stat-card-primary .stat-caption { color: #8eafa5; }
.stat-card-primary .stat-icon-wrap { background: #2e514d; color: #c5ddbb; }
.data-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; overflow: hidden; box-shadow: var(--shadow-sm); }
.data-card-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 25px 25px 21px; }
.data-card-heading h2 { display: flex; align-items: center; gap: 9px; font-size: 16px; font-weight: 600; margin: 0; }
.data-card-heading h2 span { font-size: 10px; font-weight: 500; color: var(--primary); background: var(--bg-tag-info); border-radius: 5px; padding: 2px 7px; }
.data-card-heading p { margin: 6px 0 0; color: var(--text-muted); font-size: 11px; }
.toolbar-actions, .search-controls, .filter-actions { display: flex; gap: 8px; align-items: center; }
.search-controls { flex: 1; min-width: 0; }
.filter-actions { flex-shrink: 0; }
.refresh-button { color: var(--text-secondary); flex-shrink: 0; }
.btn-ghost { background: var(--bg-card); color: var(--text-secondary); border: 1px solid var(--border-color); }
.btn-ghost:hover { color: var(--primary); border-color: var(--border-strong); background: var(--bg-hover); }
.toolbar { border-top: 1px solid var(--border-light); display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 16px 25px; }
.list-label { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--primary); font-weight: 600; }
.list-label span { width: 5px; height: 5px; background: var(--primary); border-radius: 50%; }
.toolbar-search { width: 300px; position: relative; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: var(--text-muted); z-index: 1; pointer-events: none; font-size: 15px; }
.toolbar-search :deep(.el-input__wrapper) { padding-left: 35px; background: var(--bg-hover) !important; box-shadow: none !important; }
.toolbar-search :deep(.el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px var(--primary) inset !important; }
.table-wrap { overflow-x: auto; }
.list-skeleton { padding: 30px; }
.patient-table :deep(.el-table__header-wrapper th.el-table__cell) { background: var(--bg-hover) !important; color: var(--text-secondary) !important; font-weight: 500 !important; font-size: 11px; padding: 12px 0; border-bottom: 1px solid var(--border-light); }
.patient-table :deep(td.el-table__cell) { padding: 16px 0; border-bottom: 1px solid var(--border-light); }
.patient-table :deep(.el-table__row:hover > td.el-table__cell) { background: var(--bg-hover) !important; }
.row-index, .col-header { color: var(--text-muted); font-size: 10px; font-weight: 400; }
.patient-info { display: flex; align-items: center; gap: 11px; }
.patient-avatar { width: 35px; height: 35px; flex-shrink: 0; border-radius: 11px; display: grid; place-items: center; color: #fff; font-size: 12px; font-weight: 500; }
.patient-name { display: block; color: var(--text-primary); font-size: 12px; font-weight: 600; border: none; padding: 0; background: none; cursor: pointer; text-align: left; }
.patient-name:hover { color: var(--primary); }
.patient-id { font-size: 9px; margin-top: 3px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.gender-tag { font-size: 11px; color: var(--text-secondary); }
.gender-male { color: #5c8094; }
.gender-female { color: #a87f8a; }
.age-value { font-size: 12px; color: var(--text-primary); }
.age-value small { font-size: 9px; color: var(--text-muted); margin-left: 2px; }
.record-no { font-size: 11px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
.detect-time { display: inline-flex; align-items: center; gap: 6px; font-size: 10px; color: var(--text-secondary); }
.detect-time .el-icon { color: var(--text-muted); font-size: 12px; }
.detect-count { margin-top: 3px; font-size: 9px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.status-pill { display: inline-flex; align-items: center; gap: 5px; padding: 3px 8px; border-radius: 5px; font-size: 10px; white-space: nowrap; }
.status-dot { width: 4px; height: 4px; border-radius: 50%; background: currentColor; }
.status-success { background: var(--bg-tag-success); color: var(--success); }
.status-danger { background: var(--bg-tag-danger); color: var(--danger); }
.status-warning { background: var(--bg-tag-warning); color: var(--warning); }
.status-default { background: var(--bg-tag-info); color: var(--primary); }
.action-group { display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }
.row-upload, .row-detail, .row-more { display: inline-flex; align-items: center; justify-content: center; height: 34px; border: 0; border-radius: 7px; cursor: pointer; font-size: 11px; white-space: nowrap; }
.row-upload { gap: 5px; padding: 0 10px; background: var(--bg-tag-info); color: var(--primary); font-weight: 600; }
.row-upload .el-icon { font-size: 14px; }
.row-upload:hover { background: var(--primary-light); }
.row-detail { padding: 0 3px; background: transparent; color: var(--text-secondary); }
.row-detail:hover { color: var(--primary); background: var(--bg-hover); }
.row-more { width: 32px; background: transparent; color: var(--text-secondary); font-size: 16px; }
.row-more:hover { background: var(--bg-hover); color: var(--primary); }
.pagination-bar { display: flex; align-items: center; justify-content: space-between; padding: 18px 25px; gap: 16px; }
.pagination-info { font-size: 10px; color: var(--text-muted); }
.pagination-info strong { color: var(--text-primary); font-weight: 500; }
.empty-state { text-align: center; padding: 65px 20px; }
.empty-icon { width: 68px; height: 68px; display: inline-grid; place-items: center; border-radius: 21px; color: var(--primary); background: var(--bg-tag-info); margin-bottom: 18px; }
.empty-icon .el-icon { font-size: 30px; }
.empty-title { font-size: 15px; font-weight: 500; color: var(--text-primary); margin: 0 0 7px; }
.empty-desc { font-size: 11px; margin: 0 0 22px; color: var(--text-muted); }
.list-footnote { display: flex; align-items: center; justify-content: center; gap: 6px; color: var(--text-muted); font-size: 10px; margin-top: 18px; }
.list-footnote .el-icon { flex-shrink: 0; }
.dialog-body { padding: 16px 12px 0; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; }
@media (max-width: 1200px) { .meta-badge { display: none; } .stat-card-inner { padding: 21px 18px; } .stat-value { font-size: 32px; } }
@media (max-width: 980px) { .stats-row { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 760px) {
  .page-header { align-items: flex-start; flex-wrap: wrap; gap: 15px; margin-bottom: 22px; }
  .page-title { font-size: 26px; }
  .page-desc { font-size: 11px; max-width: 240px; line-height: 1.8; }
  .page-header-meta .el-button { height: 44px; padding: 0 16px; font-size: 12px; }
  .stats-row { gap: 10px; margin-bottom: 22px; }
  .stat-card-inner { padding: 18px 16px; gap: 5px; }
  .stat-icon-wrap { width: 30px; height: 30px; border-radius: 8px; }
  .stat-icon-wrap .el-icon { font-size: 16px !important; }
  .stat-value { font-size: 29px; }
  .stat-label { font-size: 11px; margin-bottom: 12px; }
  .stat-caption { font-size: 9px; }
  .data-card-heading { align-items: flex-start; padding: 20px 17px; }
  .data-card-heading h2 { font-size: 15px; }
  .data-card-heading p { display: none; }
  .toolbar-actions .el-button { padding: 7px 9px; font-size: 10px; height: 30px; }
  .toolbar { flex-wrap: wrap; align-items: stretch; padding: 14px 17px; gap: 10px; }
  .search-controls { flex-wrap: wrap; flex-basis: 100%; }
  .toolbar-search { width: 100%; flex-basis: 100%; }
  .toolbar-search :deep(.el-input__wrapper) { min-height: 44px; }
  .filter-actions { flex: 1; }
  .filter-actions .el-button { flex: 1; min-height: 44px; }
  .refresh-button { margin-left: auto; min-height: 36px; }
  .action-group { gap: 4px; }
  .row-detail { display: none; }
  .row-upload { height: 40px; padding: 0 8px; }
  .row-more { width: 40px; height: 40px; }
  .pagination-bar { padding: 15px 17px; gap: 10px; flex-wrap: wrap; justify-content: center; }
  .list-footnote { align-items: flex-start; font-size: 9px; text-align: center; line-height: 1.7; }
  .list-footnote .el-icon { margin-top: 3px; }
  .dialog-body { padding-left: 0; padding-right: 0; }
}
</style>
