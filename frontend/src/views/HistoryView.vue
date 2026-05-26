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
      <div class="card-header">
        <div class="card-header-left">
          <div class="card-icon">
            <el-icon><Document /></el-icon>
          </div>
          <h3>检测记录列表</h3>
        </div>
      </div>

      <div class="table-wrap">
        <el-table :data="tableData" v-loading="loading" class="history-table">
          <template #empty>
            <div class="empty-state">
              <div class="empty-icon">
                <el-icon :size="48"><Document /></el-icon>
              </div>
              <p class="empty-title">暂无检测记录</p>
              <p class="empty-desc">上传超声影像后将自动生成检测记录</p>
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

          <el-table-column label="置信度" width="140">
            <template #default="{ row }">
              <div class="confidence-cell">
                <span class="confidence-text">{{ confidenceText(row.confidence) }}</span>
                <div class="confidence-bar">
                  <div
                    class="confidence-fill"
                    :style="{ width: confidenceText(row.confidence), background: confidenceColor(row.confidence) }"
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
                <span>{{ row.created_at }}</span>
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
import { Document, Warning, Select, DataLine, Clock, View } from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import { getResults } from '../api/results'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)

const positiveCount = computed(() =>
  tableData.value.filter((r) => r.classification === '肠套叠阳性').length
)
const negativeCount = computed(() =>
  tableData.value.filter((r) => r.classification === '肠套叠阴性').length
)
const avgConfidence = computed(() => {
  const vals = tableData.value.map((r) => r.confidence).filter((v) => v != null)
  if (vals.length === 0) return 0
  return vals.reduce((a, b) => a + b, 0) / vals.length
})

const statItems = computed(() => [
  {
    label: '总检测数',
    value: tableData.value.length,
    icon: Document,
    color: 'var(--primary)',
  },
  {
    label: '阳性病例',
    value: positiveCount.value,
    icon: Warning,
    color: 'var(--danger)',
  },
  {
    label: '阴性病例',
    value: negativeCount.value,
    icon: Select,
    color: 'var(--success)',
  },
  {
    label: '平均置信度',
    value: (avgConfidence.value * 100).toFixed(0) + '%',
    icon: DataLine,
    color: 'var(--warning)',
  },
])

function resultClass(classification) {
  if (classification === '肠套叠阳性') return 'status-danger'
  if (classification === '肠套叠阴性') return 'status-success'
  if (classification === '图像质量不佳') return 'status-warning'
  return 'status-default'
}

function confidenceText(val) {
  if (val === null || val === undefined) return '—'
  return Math.round(val * 100) + '%'
}

function confidenceColor(val) {
  if (val == null) return 'var(--text-muted)'
  const pct = val * 100
  if (pct >= 80) return 'var(--success)'
  if (pct >= 50) return 'var(--warning)'
  return 'var(--danger)'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getResults({ page: page.value, size: size.value })
    tableData.value = res.data.items ?? res.data.data ?? res.data
    total.value = res.data.total ?? 0
  } catch {
    ElMessage.error('获取检测记录失败')
  } finally {
    loading.value = false
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
  flex-shrink: 0;
  transition: opacity 0.2s ease;
}
.stat-card:hover .stat-icon-wrap {
  opacity: 0.15;
}
.stat-icon-wrap .el-icon {
  color: var(--accent);
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
.history-table :deep(.el-table__header-wrapper th.el-table__cell) {
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
}
</style>
