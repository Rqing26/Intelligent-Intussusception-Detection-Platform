<template>
  <AppLayout>
    <div class="history-view">
      <h3 class="page-title">检测记录</h3>

      <el-table :data="tableData" v-loading="loading" border stripe style="width: 100%">
        <template #empty>
          <div class="empty-state">暂无检测记录</div>
        </template>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="诊断结果" width="140">
          <template #default="{ row }">
            <el-tag size="small" effect="dark" :type="tagType(row.classification)">
              {{ row.classification }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="100">
          <template #default="{ row }">
            {{ confidenceText(row.confidence) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="treatment_advice"
          label="治疗建议"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column label="检测时间" width="180">
          <template #default="{ row }">{{ row.created_at }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="$router.push(`/results/${row.id}`)">
              查看详情
            </el-link>
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
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppLayout from '../components/AppLayout.vue'
import { getResults } from '../api/results'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const size = ref(10)
const total = ref(0)

function tagType(classification) {
  const map = {
    '肠套叠阳性': 'danger',
    '肠套叠阴性': 'success',
    '图像质量不佳': 'warning',
  }
  return map[classification] || 'info'
}

function confidenceText(val) {
  if (val === null || val === undefined) return '-'
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
.history-view {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.page-title {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.empty-state {
  padding: 60px 0;
  color: #909399;
}
</style>
