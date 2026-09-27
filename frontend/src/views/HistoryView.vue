<template>
  <AppLayout>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <h1 class="page-title">检测记录</h1>
        <p class="page-desc">查看所有超声影像的AI检测结果与诊断分析</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card" v-for="(stat, idx) in statItems" :key="idx">
        <div class="stat-card-inner">
          <div class="stat-body">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
          <!-- 卡片版式与「患者管理」保持一致：数字在左、图标片在右 -->
          <div
            class="stat-icon-wrap"
            :style="{ '--accent': stat.color, '--accent-tint': `var(${stat.tint})` }"
          >
            <el-icon :size="20"><component :is="stat.icon" /></el-icon>
          </div>
        </div>
        <div class="stat-accent-bar" :style="{ background: stat.color }"></div>
      </div>
    </div>

    <!-- 数据卡片 -->
    <div class="data-card">
      <div class="card-header">
        <div class="card-header-left">
          <div class="card-icon">
            <el-icon><Document /></el-icon>
          </div>
          <h3>检测记录列表</h3>
        </div>
        <el-button :icon="Download" @click="handleExport" :loading="exporting">导出 CSV</el-button>
      </div>

      <!-- 筛选工具栏 -->
      <div class="filter-bar">
        <div class="filter-search">
          <el-icon class="search-icon"><Search /></el-icon>
          <el-input v-model="search" placeholder="按患者姓名搜索..." clearable @keyup.enter="handleSearch" />
        </div>
        <el-select v-model="classification" placeholder="按诊断结论筛选" clearable style="width: 180px" @change="handleSearch">
          <el-option label="肠套叠阳性" value="肠套叠阳性" />
          <el-option label="肠套叠阴性" value="肠套叠阴性" />
          <el-option label="图像质量不佳" value="图像质量不佳" />
        </el-select>
      </div>

      <div class="table-wrap">
        <template v-if="loading && !tableData.length">
          <el-skeleton :rows="6" animated class="list-skeleton" />
        </template>
        <el-table v-else :data="tableData" v-loading="loading" class="history-table">
          <template #empty>
            <div class="empty-state">
              <div class="empty-icon">
                <el-icon :size="48"><Document /></el-icon>
              </div>
              <p class="empty-title">{{ search || classification ? '未找到符合条件的记录' : '暂无检测记录' }}</p>
              <p class="empty-desc">{{ search || classification ? '调整筛选条件后重试' : '上传超声影像后将自动生成检测记录' }}</p>
              <el-button v-if="!search && !classification" type="primary" @click="$router.push('/patients')">前往患者管理</el-button>
            </div>
          </template>

          <el-table-column type="index" width="56" align="center">
            <template #header>#</template>
            <template #default="{ $index }">
              <span class="row-index">{{ (page - 1) * size + $index + 1 }}</span>
            </template>
          </el-table-column>

          <el-table-column label="诊断结果" width="150" align="center">
            <template #default="{ row }">
              <span class="status-pill" :class="resultClass(row.classification)">
                <span class="status-dot"></span>
                {{ row.classification }}
              </span>
            </template>
          </el-table-column>

          <!-- 展示模型真实输出「检测证据分」；不再展示由精度表换算的置信度百分比 -->
          <el-table-column label="证据分" width="140">
            <template #default="{ row }">
              <div class="confidence-cell">
                <span class="confidence-text">{{ evidenceText(row.detection_score) }}</span>
                <div class="confidence-bar">
                  <div
                    class="confidence-fill"
                    :style="{
                      width: evidenceBarWidth(row.detection_score),
                      background: evidenceColor(row.detection_score),
                    }"
                  />
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="treatment_advice" label="治疗建议" min-width="240" show-overflow-tooltip
          >
            <template #default="{ row }">
              <span class="advice-text">{{ row.treatment_advice || '—' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="检测时间" width="170">
            <template #default="{ row }">
              <div class="detect-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatDateTime(row.created_at) }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" fixed="right" align="center">
            <template #default="{ row }">
              <el-tooltip content="查看详情" placement="top">
                <button class="icon-btn" @click="$router.push(`/results/${row.id}`)">
                  <el-icon><View /></el-icon>
                </button>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>

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
import { Document, Warning, Select, Clock, View, Download, Search } from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import { getResults, getResultsStats, exportResults } from '../api/results'
import { formatDateTime } from '../utils/time'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)
const exporting = ref(false)
const search = ref('')
const classification = ref('')

const stats = ref({
  total: 0,
  positive: 0,
  negative: 0,
  poor_quality: 0,
  avg_confidence: 0,
  positive_rate: 0,
  negative_rate: 0,
  poor_quality_rate: 0,
  confirm_total: 0,
})

const pct = (v) => Math.round((v || 0) * 100) + '%'

const statItems = computed(() => [
  {
    label: '总检测数',
    value: stats.value.total,
    icon: Document,
    color: 'var(--primary)',
    tint: '--bg-tag-info',
  },
  {
    label: `阳性病例 (${pct(stats.value.positive_rate)})`,
    value: stats.value.positive,
    icon: Warning,
    color: 'var(--danger)',
    tint: '--bg-tag-danger',
  },
  {
    label: `阴性病例 (${pct(stats.value.negative_rate)})`,
    value: stats.value.negative,
    icon: Select,
    color: 'var(--success)',
    tint: '--bg-tag-success',
  },
  // 概览不再显示「平均参考精度」：该值是用评估集精度表换算出来的查表值，
  // 全平台共用一张表求和取均值没有临床含义（见 docs/准确率与置信度核实.md）
])

function resultClass(classification) {
  if (classification === '肠套叠阳性') return 'status-danger'
  if (classification === '肠套叠阴性') return 'status-success'
  if (classification === '图像质量不佳') return 'status-warning'
  return 'status-default'
}

// ── 「检测证据分」展示：模型真实输出，非查表换算的百分比 ──
// 本平台实测参考区间：真实超声阳性约 0.76~0.91，阴性约 0；判界阈值仅 0.0145，
// 因此条形图按 1.0 满量程显示（不要把 0.8 读成"80% 把握"）。
function evidenceText(val) {
  if (val === null || val === undefined) return '—'
  return Number(val).toFixed(3)
}

function evidenceBarWidth(val) {
  if (val == null) return '0%'
  return Math.max(0, Math.min(1, Number(val))) * 100 + '%'
}

function evidenceColor(val) {
  if (val == null) return 'var(--text-muted)'
  const v = Number(val)
  if (v >= 0.5) return 'var(--success)'
  if (v >= 0.014451) return 'var(--warning)'   // 达到判界阈值
  return 'var(--text-muted)'
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, size: size.value }
    if (search.value) params.patient_search = search.value
    if (classification.value) params.classification = classification.value
    const res = await getResults(params)
    tableData.value = res.data.items ?? res.data.data ?? res.data
    total.value = res.data.total ?? 0
    const statsRes = await getResultsStats()
    stats.value = statsRes.data
  } catch {
    ElMessage.error('获取检测记录失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchData()
}

async function handleExport() {
  exporting.value = true
  try {
    const res = await exportResults({})
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'results.csv'
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(fetchData)
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

/* 统计卡片 */
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
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px 22px;
  min-height: 96px;
}
.stat-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  /* 半透明底色 + 实色图标；不能对容器用 opacity，否则图标会一起变透明 */
  background: var(--accent-tint, var(--bg-hover));
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.25s ease;
}
.stat-card:hover .stat-icon-wrap {
  transform: scale(1.06);
}
.stat-icon-wrap .el-icon {
  color: inherit;
}
.stat-body {
  flex: 1;
  min-width: 0;
}
.stat-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.05;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}
.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 6px;
  font-weight: 500;
  letter-spacing: 0.02em;
  white-space: nowrap;
}
.stat-accent-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  opacity: 0.9;
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

/* 筛选工具栏 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
}
.filter-search {
  position: relative;
  width: 320px;
}
.filter-search .search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 16px;
  z-index: 1;
  pointer-events: none;
}
.filter-search :deep(.el-input__wrapper) {
  padding-left: 36px !important;
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
.list-skeleton {
  padding: 20px;
}.history-table :deep(.el-table__header-wrapper th.el-table__cell) {
  background: var(--bg-page) !important;
  color: var(--text-secondary) !important;
  font-weight: 600 !important;
  font-size: 12px;
  text-transform: none;
  letter-spacing: 0;
  border-bottom: 1px solid var(--border-color);
  padding: 12px 0;
}
.history-table :deep(.el-table__row:hover > td.el-table__cell) {
  background: var(--bg-hover) !important;
}
.history-table :deep(td.el-table__cell) {
  padding: 14px 0;
  border-bottom: 1px solid var(--border-light);
}

.row-index {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-display);
  font-weight: 500;
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

/* 置信度 */
.confidence-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.confidence-text {
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--text-primary);
  font-size: 13px;
}
.confidence-bar {
  width: 80px;
  height: 4px;
  background: var(--border-light);
  border-radius: 2px;
  overflow: hidden;
}
.confidence-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}

/* 治疗建议 */
.advice-text {
  font-size: 13px;
  color: var(--text-secondary);
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

/* 操作按钮 */
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

/* 分页 */
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

/* 空状态 */
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
  margin: 0;
}

@media (max-width: 1100px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
  .pagination-bar {
    flex-direction: column;
    gap: 12px;
  }
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-search {
    width: 100%;
  }
}
</style>
