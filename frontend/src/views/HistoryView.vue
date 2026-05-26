<template>
  <AppLayout>
    <div class="page-header-row">
      <div>
        <h2 class="page-title">检测记录</h2>
        <div class="breadcrumb">首页 / 检测记录</div>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div>
          <div class="stat-value">{{ tableData.length }}</div>
          <div class="stat-label">总检测数</div>
        </div>
        <div class="stat-icon">📋</div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-value">{{ positiveCount }}</div>
          <div class="stat-label">阳性病例</div>
        </div>
        <div class="stat-icon">⚠</div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-value">{{ negativeCount }}</div>
          <div class="stat-label">阴性病例</div>
        </div>
        <div class="stat-icon">✓</div>
      </div>
      <div class="stat-card">
        <div>
          <div class="stat-value">{{ avgConfidence }}</div>
          <div class="stat-label">平均置信度</div>
        </div>
        <div class="stat-icon">%</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3>检测记录列表</h3>
      </div>
      <div class="card-body">
        <el-table :data="tableData" v-loading="loading" style="width: 100%">
          <template #empty>
            <div class="empty-state">暂无检测记录</div>
          </template>
          <el-table-column prop="id" label="ID" width="70">
            <template #default="{ row }">
              <strong style="font-family: var(--font-display)">#{{ row.id }}</strong>
            </template>
          </el-table-column>
          <el-table-column label="诊断结果" width="140">
            <template #default="{ row }">
              <span :class="['seal-tag', resultClass(row.classification)]">
                {{ row.classification }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="置信度" width="110">
            <template #default="{ row }">
              <span class="confidence-text">{{ confidenceText(row.confidence) }}</span>
            </template>
          </el-table-column>
          <el-table-column
            prop="treatment_advice"
            label="治疗建议"
            min-width="220"
            show-overflow-tooltip
          />
          <el-table-column label="检测时间" width="180">
            <template #default="{ row }">{{ row.created_at }}</template>
          </el-table-column>
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <div class="action-group">
                <span class="action-btn" @click="$router.push(`/results/${row.id}`)">查看详情</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
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
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppLayout from '../components/AppLayout.vue'
import { getResults } from '../api/results'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)

const positiveCount = computed(() =>
  tableData.value.filter(r => r.classification === '肠套叠阳性').length
)
const negativeCount = computed(() =>
  tableData.value.filter(r => r.classification === '肠套叠阴性').length
)
const avgConfidence = computed(() => {
  const vals = tableData.value.map(r => r.confidence).filter(v => v != null)
  if (vals.length === 0) return '—'
  const avg = vals.reduce((a, b) => a + b, 0) / vals.length
  return Math.round(avg * 100) + '%'
})

function resultClass(classification) {
  if (classification === '肠套叠阳性') return 'seal-vermillion'
  if (classification === '肠套叠阴性') return 'seal-malachite'
  if (classification === '图像质量不佳') return 'seal-gold'
  return 'seal-ink'
}

function confidenceText(val) {
  if (val === null || val === undefined) return '—'
  return Math.round(val * 100) + '%'
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
.card-body {
  padding: 0;
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

.confidence-text {
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--text-primary);
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
