<template>
  <AppLayout>
    <div class="patient-detail">
      <el-page-header icon="" @back="$router.push('/patients')">
        <template #content>
          <span class="page-title">患者详情</span>
        </template>
      </el-page-header>

      <div class="content-wrapper" v-loading="loading">
        <template v-if="patient">
          <el-descriptions :column="2" border class="info-card">
            <el-descriptions-item label="姓名">{{ patient.name }}</el-descriptions-item>
            <el-descriptions-item label="性别">{{ patient.gender }}</el-descriptions-item>
            <el-descriptions-item label="年龄(月)">{{ patient.age }}</el-descriptions-item>
            <el-descriptions-item label="病历号">{{ patient.medical_record_no }}</el-descriptions-item>
            <el-descriptions-item label="临床症状" :span="2">{{ patient.clinical_symptoms }}</el-descriptions-item>
            <el-descriptions-item label="创建时间" :span="2">{{ patient.created_at }}</el-descriptions-item>
          </el-descriptions>

          <div class="section-header">
            <h3>超声影像</h3>
            <el-button type="primary" @click="$router.push(`/patients/${patient.id}/upload`)">
              上传新影像
            </el-button>
          </div>

          <el-table :data="images" border stripe style="width: 100%">
            <template #empty>
              <div class="empty-state">暂无超声影像数据</div>
            </template>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="filename" label="文件名" min-width="180" />
            <el-table-column label="上传时间" width="180">
              <template #default="{ row }">{{ row.uploaded_at }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.has_result ? 'success' : 'info'" size="small">
                  {{ row.has_result ? '已检测' : '待检测' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-link type="primary" :underline="false" @click="previewImage(row)">预览</el-link>
                <el-link
                  v-if="!row.has_result"
                  type="warning"
                  :underline="false"
                  style="margin-left: 8px"
                  @click="handleDetect(row)"
                >
                  检测
                </el-link>
                <el-link
                  v-if="row.has_result"
                  type="primary"
                  :underline="false"
                  style="margin-left: 8px"
                  @click="$router.push(`/results/${row.result_id}`)"
                >
                  查看结果
                </el-link>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </div>

      <el-dialog v-model="previewVisible" title="影像预览" width="700px">
        <ImageViewer v-if="previewSrc" :src="previewSrc" />
      </el-dialog>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppLayout from '../components/AppLayout.vue'
import ImageViewer from '../components/ImageViewer.vue'
import { getPatient } from '../api/patients'
import { getImageInfo, getImageUrl, runDetection } from '../api/images'

const route = useRoute()
const loading = ref(false)
const patient = ref(null)
const images = ref([])
const previewVisible = ref(false)
const previewSrc = ref('')

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

onMounted(fetchPatient)
</script>

<style scoped>
.patient-detail {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.content-wrapper {
  margin-top: 20px;
}

.info-card {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.empty-state {
  padding: 60px 0;
  color: #909399;
}
</style>
