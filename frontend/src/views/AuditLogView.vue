<template>
  <AppLayout>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <span class="page-eyebrow">ACTIVITY & AUDIT</span>
        <h1 class="page-title">审计日志</h1>
        <p class="page-desc">查阅系统操作轨迹，让每次更改变得清晰可追溯。</p>
      </div>
      <span class="access-badge"><el-icon><Lock /></el-icon>管理员工作区</span>
    </div>

    <!-- 数据卡片 -->
    <div class="data-card">
      <div class="audit-card-heading"><div><h3>操作记录</h3><p>按时间、操作对象或关键词检索</p></div><el-button class="export-button" :icon="Download" @click="handleExport" :loading="exporting">{{ exporting ? '正在导出' : '导出 CSV' }}</el-button></div>
      <!-- 工具栏 -->
      <div class="toolbar" role="search" aria-label="筛选审计日志">
        <div class="filter-fields">
          <div class="filter-field">
            <label class="filter-label" for="audit-keyword">关键词</label>
            <div class="toolbar-search">
              <el-icon class="search-icon"><Search /></el-icon>
              <el-input
                id="audit-keyword"
                v-model="search"
                placeholder="用户名、操作或详情"
                clearable
                @keyup.enter="handleSearch"
                @clear="handleSearch"
              />
            </div>
          </div>
          <div class="filter-field">
            <label class="filter-label" for="audit-resource">操作对象</label>
            <el-select id="audit-resource" v-model="resource" placeholder="全部操作对象" clearable @change="handleSearch">
              <el-option label="患者" value="patient" />
              <el-option label="影像/检测" value="image" />
              <el-option label="系统设置" value="settings" />
              <el-option label="登录" value="auth" />
            </el-select>
          </div>
          <div class="filter-field date-field">
            <label class="filter-label" for="audit-start-time">时间范围</label>
            <el-date-picker
              :id="['audit-start-time', 'audit-end-time']"
              v-model="dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              @change="handleSearch"
            />
          </div>
        </div>
        <div class="toolbar-actions">
          <el-button type="primary" :icon="Search" :loading="tableLoading" @click="handleSearch">查询日志</el-button>
          <el-button :disabled="!hasFilters || tableLoading" @click="resetFilters">重置筛选</el-button>
        </div>
      </div>

      <!-- 表格 -->
      <div class="table-wrap">
        <el-table :data="tableData" v-loading="tableLoading" class="audit-table">
          <template #empty>
            <div class="empty-state">
              <div class="empty-icon">
                <el-icon :size="48"><Document /></el-icon>
              </div>
              <p class="empty-title">暂无审计记录</p>
              <p class="empty-desc">系统会在这里记录医护人员的操作</p>
            </div>
          </template>

          <el-table-column label="时间" width="170">
            <template #default="{ row }">
              <div class="detect-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatDateTime(row.created_at) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="username" label="操作人" width="120">
            <template #default="{ row }">
              <span class="username-text">{{ row.username || '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="110" align="center">
            <template #default="{ row }">
              <span class="action-pill" :class="actionClass(row.action)">
                {{ actionText(row.action) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="对象" width="110" align="center">
            <template #default="{ row }">
              <span class="resource-tag">{{ resourceText(row.resource) }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="detail" label="详情" min-width="240" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="detail-text">{{ row.detail || '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="ip_address" label="来源 IP" width="140">
            <template #default="{ row }">
              <span class="ip-text">{{ row.ip_address || '—' }}</span>
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
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Clock, Search, Download, Lock } from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import { getAuditLogs, exportAuditLogs } from '../api/audit'
import { formatDateTime } from '../utils/time'

const tableData = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const tableLoading = ref(false)
const search = ref('')
const resource = ref('')
const dateRange = ref(null)
const exporting = ref(false)
const hasFilters = computed(() => Boolean(search.value || resource.value || dateRange.value?.length))

const RESOURCE_MAP = {
  patient: '患者',
  image: '影像/检测',
  settings: '系统设置',
  auth: '登录',
}

const ACTION_MAP = {
  create: '新增',
  update: '编辑',
  delete: '删除',
  upload: '上传',
  detect: '检测',
  login: '登录',
  logout: '退出',
}

function resourceText(r) {
  return RESOURCE_MAP[r] || r || '—'
}

function actionText(a) {
  return ACTION_MAP[a] || a || '—'
}

function actionClass(a) {
  if (a === 'delete') return 'act-danger'
  if (a === 'create' || a === 'upload') return 'act-primary'
  if (a === 'detect') return 'act-warning'
  return 'act-default'
}

function buildParams() {
  const params = {
    search: search.value,
    resource: resource.value,
    page: page.value,
    size: size.value,
  }
  if (Array.isArray(dateRange.value) && dateRange.value.length === 2) {
    const [s, e] = dateRange.value
    if (s) params.start = new Date(s).toISOString()
    if (e) params.end = new Date(e).toISOString()
  }
  return params
}

async function fetchData() {
  tableLoading.value = true
  try {
    const res = await getAuditLogs(buildParams())
    tableData.value = res.data.items ?? res.data.data ?? res.data
    total.value = res.data.total ?? 0
  } catch {
    ElMessage.error('获取审计日志失败')
  } finally {
    tableLoading.value = false
  }
}

async function handleExport() {
  if (exporting.value) return
  exporting.value = true
  try {
    const params = buildParams()
    delete params.page
    delete params.size
    const res = await exportAuditLogs(params)
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'audit_logs.csv'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function resetFilters() {
  search.value = ''
  resource.value = ''
  dateRange.value = null
  handleSearch()
}

onMounted(fetchData)
</script>

<style scoped>
.access-badge { display: inline-flex; align-items: center; gap: 7px; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-secondary); font-size: 11px; background: var(--bg-card); }
.audit-card-heading { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; padding: 24px; border-bottom: 1px solid var(--border-light); }
.audit-card-heading h3 { margin: 0 0 6px; color: var(--text-primary); font-size: 16px; font-weight: 650; }
.audit-card-heading p { margin: 0; color: var(--text-muted); font-size: 12px; }

.page-eyebrow {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: var(--primary);
}

.page-header {
  display: flex;
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

.data-card {
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 24px rgba(23, 50, 57, 0.025);
  overflow: hidden;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  padding: 18px 24px;
  gap: 16px;
  border-bottom: 1px solid var(--border-light);
}
.filter-fields {
  flex: 1 1 680px;
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(130px, 0.65fr) minmax(260px, 1.3fr);
  gap: 12px;
  min-width: 0;
}
.filter-field { min-width: 0; }
.filter-label { display: block; margin-bottom: 9px; font-size: 12px; font-weight: 500; color: var(--text-secondary); }
.filter-field .el-select, .filter-field .el-date-editor { width: 100%; min-width: 0; }
.filter-field :deep(.el-input__wrapper), .filter-field :deep(.el-select__wrapper), .filter-field :deep(.el-range-editor) { min-height: 44px; }
.export-button { min-height: 40px; color: var(--text-secondary); background: var(--bg-card); border-color: var(--border-color); }
.export-button:hover { color: var(--primary); border-color: var(--primary); background: var(--bg-hover); }
.toolbar-search {
  position: relative;
  width: 100%;
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
  flex-wrap: wrap;
  gap: 8px;
  margin-left: auto;
}
.toolbar-actions .el-button { min-height: 44px; margin-left: 0; padding: 0 17px; }

.table-wrap {
  min-width: 0;
  padding: 0;
  overflow-x: auto;
}

.audit-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: var(--bg-page) !important;
  color: var(--text-secondary) !important;
  font-weight: 600 !important;
  font-size: 12px;
  border-bottom: 1px solid var(--border-color);
  padding: 12px 0;
}
.audit-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: var(--bg-hover) !important;
}
.audit-table :deep(td.el-table__cell) {
  padding: 14px 0;
  border-bottom: 1px solid var(--border-light);
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

.username-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.action-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.act-primary {
  background: var(--bg-tag-info);
  color: var(--primary);
}
.act-danger {
  background: var(--bg-tag-danger);
  color: var(--danger);
}
.act-warning {
  background: var(--bg-tag-warning);
  color: var(--warning);
}
.act-default {
  background: var(--bg-tag-success);
  color: var(--success);
}

.resource-tag {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 2px 8px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}

.detail-text {
  font-size: 13px;
  color: var(--text-secondary);
}
.ip-text {
  font-family: var(--font-display);
  font-size: 12px;
  color: var(--text-muted);
}

.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 24px;
  border-top: 1px solid var(--border-light);
  background: var(--bg-card);
}
.pagination-info {
  font-size: 12px;
  color: var(--text-muted);
}
.pagination-info strong {
  color: var(--text-primary);
  font-weight: 600;
}

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

@media (max-width: 1100px) {
  .filter-fields { grid-template-columns: minmax(0, 1fr) minmax(150px, 0.7fr); }
  .date-field { grid-column: 1 / -1; }
}
@media (max-width: 640px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 16px; }
  .toolbar { flex-direction: column; align-items: stretch; padding: 18px; }
  .filter-fields { flex-basis: auto; grid-template-columns: minmax(0, 1fr); }
  .toolbar-actions { width: 100%; margin-left: 0; }
  .toolbar-actions .el-button { flex: 1 1 110px; }
  .export-button { min-height: 44px; }
  .pagination-bar { flex-direction: column; gap: 12px; }
  .audit-card-heading { align-items: flex-start; padding: 18px; }
}
</style>
