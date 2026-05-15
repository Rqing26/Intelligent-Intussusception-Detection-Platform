<template>
  <AppLayout>
    <div class="patient-list">
      <div class="toolbar">
        <el-input
          v-model="search"
          placeholder="搜索患者姓名或病历号"
          clearable
          style="width: 280px"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Plus" @click="openCreate">新增患者</el-button>
      </div>

      <el-table :data="tableData" v-loading="tableLoading" border stripe style="width: 100%">
        <template #empty>
          <div class="empty-state">
            <p>暂无患者数据</p>
            <el-button type="primary" @click="openCreate">新增第一位患者</el-button>
          </div>
        </template>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column label="年龄(月)" width="100">
          <template #default="{ row }">{{ row.age_months }}</template>
        </el-table-column>
        <el-table-column prop="medical_record_no" label="病历号" min-width="140" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-link type="primary" :underline="false" @click="handleDetail(row.id)">详情</el-link>
            <el-link type="primary" :underline="false" @click="openEdit(row)" style="margin-left: 8px">编辑</el-link>
            <el-popconfirm
              title="确定删除该患者吗？"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-link type="danger" :underline="false" style="margin-left: 8px">删除</el-link>
              </template>
            </el-popconfirm>
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

      <el-dialog
        v-model="dialogVisible"
        :title="editingId ? '编辑患者' : '新增患者'"
        width="520px"
        :close-on-click-modal="false"
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
          <el-form-item label="年龄(月)" prop="age_months">
            <el-input-number v-model="dialogForm.age_months" :min="0" :max="144" style="width: 100%" />
          </el-form-item>
          <el-form-item label="病历号" prop="medical_record_no">
            <el-input v-model="dialogForm.medical_record_no" />
          </el-form-item>
          <el-form-item label="临床症状" prop="clinical_symptoms">
            <el-input v-model="dialogForm.clinical_symptoms" type="textarea" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
        </template>
      </el-dialog>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import { getPatients, createPatient, updatePatient, deletePatient } from '../api/patients'

const router = useRouter()

const search = ref('')
const tableData = ref([])
const tableLoading = ref(false)
const page = ref(1)
const size = ref(10)
const total = ref(0)

const dialogVisible = ref(false)
const editingId = ref(null)
const submitLoading = ref(false)
const dialogFormRef = ref(null)

const dialogForm = reactive({
  name: '',
  gender: '',
  age_months: null,
  medical_record_no: '',
  clinical_symptoms: '',
})

const dialogRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  age_months: [{ required: true, message: '请输入年龄', trigger: 'blur' }],
}

function resetDialogForm() {
  dialogForm.name = ''
  dialogForm.gender = ''
  dialogForm.age_months = null
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
  dialogForm.age_months = row.age_months
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
  } catch {
    ElMessage.error('删除失败')
  }
}

function handleDetail(id) {
  router.push(`/patients/${id}`)
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.patient-list {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
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
