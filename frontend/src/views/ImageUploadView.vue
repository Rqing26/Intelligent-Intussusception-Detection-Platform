<template>
  <AppLayout>
    <el-button class="page-back-link" text :icon="Back" :disabled="uploading" @click="$router.push(`/patients/${patientId}`)">返回患者档案</el-button>
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header-main">
        <span class="page-eyebrow">IMAGING WORKSPACE</span>
        <h1 class="page-title">上传影像</h1>
        <p class="page-desc">从一张清晰的超声影像，开始本次辅助检测。</p>
      </div>
    </div>

    <div class="workflow-strip" aria-label="影像检测流程">
      <div class="workflow-step" :class="{ current: !uploading }"><span class="step-number">01</span><div><strong>选择影像</strong><span>支持多张文件上传</span></div></div>
      <div class="workflow-step" :class="{ current: uploading }"><span class="step-number">02</span><div><strong>智能检测</strong><span>自动分析超声影像</span></div></div>
      <div class="workflow-step"><span class="step-number">03</span><div><strong>查看结果</strong><span>查看分析与打印报告</span></div></div>
    </div>

    <!-- 上传卡片 -->
    <div class="upload-layout">
      <div class="upload-card">
        <div class="card-header">
          <div class="header-icon">
            <el-icon :size="28"><Upload /></el-icon>
          </div>
          <div class="header-text">
            <h3>超声影像上传</h3>
            <p>选择本次检查的影像，确认后开始分析</p>
          </div>
        </div>

        <div class="card-body">
          <UploadZone :disabled="uploading" @file-selected="onFileSelected" />
        </div>
      </div>

      <!-- 提示卡片 -->
      <div class="tips-card">
        <span class="tips-eyebrow">BEFORE YOU UPLOAD</span>
        <div class="tips-title">
          <el-icon><InfoFilled /></el-icon>
          上传注意事项
        </div>
        <ul class="tips-list">
          <li>
            <span class="tip-num">1</span>
            请确保超声影像清晰，肠管结构可辨识
          </li>
          <li>
            <span class="tip-num">2</span>
            建议上传腹部纵切面和横切面两张影像
          </li>
          <li>
            <span class="tip-num">3</span>
            影像中应包含标尺和探头位置标记
          </li>
          <li>
            <span class="tip-num">4</span>
            上传后系统将自动进行AI检测分析
          </li>
        </ul>
      </div>
    </div>
    <div class="action-bar" role="region" aria-label="检测操作">
      <div class="selection-summary" aria-live="polite">
        <strong>{{ uploading ? `已完成 ${doneCount} / ${files.length} 张` : files.length ? `已选择 ${files.length} 张影像` : '尚未选择影像' }}</strong>
        <span>{{ uploading ? '正在上传与分析，请稍候' : files.length ? '确认文件后，即可开始本次检测' : '先选择影像，再开始检测' }}</span>
      </div>
      <el-button
        class="start-detection-button"
        type="primary"
        size="large"
        :disabled="!files.length || uploading"
        :loading="uploading"
        @click="handleUpload"
      >
        <span>{{ uploading ? '正在检测' : '开始上传并检测' }}</span>
        <el-icon v-if="!uploading" class="submit-arrow"><Right /></el-icon>
      </el-button>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Upload, InfoFilled, Back, Right } from '@element-plus/icons-vue'
import AppLayout from '../components/AppLayout.vue'
import UploadZone from '../components/UploadZone.vue'
import { uploadImage, runDetection, createDetectionTask, getDetectionTask } from '../api/images'

const route = useRoute()
const router = useRouter()

const patientId = computed(() => route.params.id)
const files = ref([])
const uploading = ref(false)
const detectProgress = ref(0)          // 当前张的检测进度
const doneCount = ref(0)               // 已完成张数

function onFileSelected(filesList) {
  files.value = filesList || []
  doneCount.value = 0
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

async function waitForTask(taskId) {
  // 轮询任务状态，直到完成或失败
  for (let i = 0; i < 180; i++) {
    const res = await getDetectionTask(taskId)
    const t = res.data?.task
    if (!t) return null
    detectProgress.value = t.progress || 0
    if (t.status === 'done') {
      return res.data?.result || { id: t.result_id }
    }
    if (t.status === 'failed') {
      throw new Error(t.error || '检测失败')
    }
    await new Promise((r) => setTimeout(r, 800))
  }
  throw new Error('检测超时')
}

async function detectOne(imageId) {
  // 提交异步检测任务，轮询进度；任务系统不可用时回退到同步接口
  const taskRes = await createDetectionTask(imageId)
  const taskId = taskRes.data?.task_id
  if (taskId) return waitForTask(taskId)
  const res = await runDetection(imageId)
  return res.data
}

async function handleUpload() {
  if (!files.value.length || uploading.value) return
  uploading.value = true
  doneCount.value = 0
  const results = []
  try {
    for (let i = 0; i < files.value.length; i++) {
      const f = files.value[i]
      // 逐张上传
      const uploadRes = await uploadImage(patientId.value, f)
      const imageId = uploadRes.data.id ?? uploadRes.data.image_id
      if (!imageId) {
        ElMessage.error(`第 ${i + 1} 张上传响应异常`)
        continue
      }
      // 逐张检测
      const result = await detectOne(imageId)
      const resultId = result?.id ?? result?.result_id
      if (resultId) results.push(resultId)
      doneCount.value = i + 1
    }

    if (results.length) {
      ElMessage.success(`已上传并检测 ${results.length} 张`)
      // 全部完成后跳到某一张结果页（这里跳到最近一张）
      router.push(`/results/${results[results.length - 1]}`)
    } else {
      ElMessage.error('检测均失败或无有效结果')
    }
  } catch (e) {
    ElMessage.error(e?.message || '上传或检测失败')
  } finally {
    uploading.value = false
  }
}

</script>

<style scoped>
.page-back-link { padding: 0; height: 28px; margin-bottom: 12px; color: var(--text-secondary); font-size: 12px; }
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

/* Upload workflow */
.workflow-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
  max-width: 900px;
  margin: 0 0 30px;
}
.workflow-step { display: flex; align-items: center; gap: 12px; color: var(--text-muted); }
.step-number {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
  background: var(--bg-card);
}
.workflow-step.current .step-number { color: #fff; background: var(--primary); border-color: var(--primary); }
.workflow-step strong { display: block; font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.workflow-step.current strong { color: var(--primary); }
.workflow-step div > span { display: block; font-size: 11px; margin-top: 4px; }
.upload-layout { display: grid; grid-template-columns: minmax(0, 1fr) 290px; gap: 24px; align-items: start; }
.upload-card {
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 24px rgba(23, 50, 57, 0.025);
  overflow: hidden;
}
.card-header { display: flex; align-items: center; gap: 14px; padding: 24px 28px; border-bottom: 1px solid var(--border-light); }
.header-icon { width: 44px; height: 44px; border-radius: 14px; background: var(--primary-glow); color: var(--primary); display: grid; place-items: center; flex-shrink: 0; }
.header-text h3 { font-size: 16px; font-weight: 650; color: var(--text-primary); margin: 0 0 5px; }
.header-text p { font-size: 12px; line-height: 1.5; color: var(--text-muted); margin: 0; }
.card-body { padding: 28px; }
.action-bar { position: sticky; bottom: 12px; z-index: 8; display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-top: 24px; padding: 18px 24px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; box-shadow: 0 -5px 24px rgba(23, 50, 57, .06); }
.selection-summary { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.selection-summary strong { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.selection-summary > span { font-size: 11px; color: var(--text-muted); }
.action-bar .el-button { margin-left: 0; }
.start-detection-button { min-width: 180px; height: 46px; flex-shrink: 0; }
.submit-arrow { margin-left: 8px; vertical-align: middle; }
.tips-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 28px 24px; position: sticky; top: 20px; }
.tips-eyebrow { font-size: 9px; font-weight: 700; letter-spacing: 0.13em; color: var(--text-muted); }
.tips-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 650; color: var(--text-primary); margin: 12px 0 24px; }
.tips-title .el-icon { color: var(--primary); }
.tips-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 22px; }
.tips-list li { display: flex; align-items: flex-start; gap: 12px; font-size: 12px; color: var(--text-secondary); line-height: 1.85; }
.tip-num { width: 22px; height: 22px; border-radius: 7px; background: var(--bg-page); color: var(--primary); display: inline-flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; margin-top: 1px; }
@media (max-width: 1100px) {
  .upload-layout { grid-template-columns: 1fr; }
  .tips-card { position: static; }
  .tips-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .page-header { flex-direction: column; align-items: flex-start; margin-bottom: 20px; }
  .workflow-strip { gap: 10px; margin-bottom: 18px; }
  .workflow-step { gap: 8px; flex-direction: column; align-items: flex-start; }
  .workflow-step div > span { display: none; }
  .card-header, .card-body { padding: 16px; }
  .action-bar { padding: 14px 16px; gap: 12px; }
  .start-detection-button { min-width: 0; padding: 0 14px; height: 46px; }
  .selection-summary strong { font-size: 12px; }
  .selection-summary > span { font-size: 10px; line-height: 1.6; }
  .tips-list { grid-template-columns: 1fr; }
}
@media (max-width: 760px) { .action-bar { bottom: calc(74px + env(safe-area-inset-bottom)); } }
</style>
