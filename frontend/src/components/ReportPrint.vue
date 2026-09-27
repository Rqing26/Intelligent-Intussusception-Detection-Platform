<template>
  <el-dialog
    v-model="visible"
    title="打印预览"
    width="900px"
    append-to-body
    @opened="onPreviewOpened"
  >
    <div class="print-actions">
      <el-button type="primary" @click="handlePrint" :loading="printing" :disabled="!result">
        <el-icon><Printer /></el-icon>导出PDF
      </el-button>
      <el-button @click="visible = false">关闭</el-button>
      <span v-if="!result" class="no-result-tip">未加载到检测结果，无法导出报告</span>
    </div>

    <div ref="reportRef" class="report-container" v-loading="printing">
      <div class="report-page">
        <!-- 医院页眉 -->
        <div class="hospital-header">
          <img src="/newlogo.png" class="hospital-logo" alt="hospital logo" />
          <div class="hospital-brand">
            <div class="hospital-name-main">
              <span class="name-part">皖南医学院</span>
              <span class="name-part sub">第一附属医院</span>
              <span class="name-part sub2">弋矶山医院</span>
            </div>
            <div class="hospital-name-en">
              THE FIRST AFFILIATED HOSPITAL OF WANNAN MEDICAL COLLEGE
            </div>
          </div>
        </div>
        <div class="header-line"></div>

        <!-- 报告标题 -->
        <div class="report-title">彩色多普勒超声检查报告</div>

        <!-- 患者信息 -->
        <div class="patient-info">
          <div class="info-row">
            <div class="info-item">
              <span class="info-label">姓　　名：</span>
              <span class="info-value">{{ patient?.name || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">性　　别：</span>
              <span class="info-value">{{ patient?.gender || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">年　　龄：</span>
              <span class="info-value">{{ patient?.age != null ? patient.age + ' 个月' : '-' }}</span>
            </div>
          </div>
          <div class="info-row">
            <div class="info-item">
              <span class="info-label">出生日期：</span>
              <span class="info-value">{{ patient?.birth_date || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">病 历 号：</span>
              <span class="info-value">{{ patient?.medical_record_no || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">住 院 号：</span>
              <span class="info-value">{{ patient?.hospital_no || '-' }}</span>
            </div>
          </div>
          <div class="info-row">
            <div class="info-item">
              <span class="info-label">检查部位：</span>
              <span class="info-value">{{ patient?.exam_part || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">申请科室：</span>
              <span class="info-value">小儿外科</span>
            </div>
            <div class="info-item">
              <span class="info-label">床　　号：</span>
              <span class="info-value">-</span>
            </div>
          </div>
          <div class="info-row">
            <div class="info-item">
              <span class="info-label">检查日期：</span>
              <span class="info-value">{{ examDate }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">报告日期：</span>
              <span class="info-value">{{ reportDate }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">检查系统：</span>
              <span class="info-value">IVSP-2</span>
            </div>
          </div>
          <div class="info-row">
            <div class="info-item wide">
              <span class="info-label">送检医院：</span>
              <span class="info-value">皖南医学院第一附属医院（弋矶山医院）</span>
            </div>
          </div>
        </div>

        <!-- 检查所见 -->
        <!--
          ⚠️ 这里以前写的是按分类硬编码的模板文本（"可见同心圆征、套筒征，CDFI 显示血流信号"），
          但模型从未输出过这些影像学征象 —— 以"超声所见"的名义写出来等于伪造检查所见。
          现改为：只陈述 AI 实际产出的内容（判定 + 证据分 + 标注区域），
          并把影像学所见明确留给检查医生。
        -->
        <div class="report-section" v-if="result">
          <div class="section-title">检查所见</div>
          <div class="section-content">
            <p class="ai-hint">{{ aiFindingHint }}</p>
            <p class="finding-rule">影像学征象描述（如"同心圆征""套筒征"、CDFI 血流信号等）须由检查医生阅片后填写，AI 不对其作任何陈述。</p>
            <p class="finding-blank">超声所见：________________________________________________________________________</p>
            <p class="finding-blank">________________________________________________________________________________</p>
          </div>
        </div>

        <!-- 超声影像 -->
        <div class="report-section" v-if="resolvedImageUrl">
          <div class="section-title">超声影像</div>
          <div class="image-wrapper">
            <img
              :src="resolvedImageUrl"
              alt="超声影像"
              class="report-image"
              @load="imageLoaded = true"
              @error="imageLoaded = true"
            />
          </div>
        </div>

        <!-- AI 辅助诊断结果 -->
        <div class="report-section" v-if="result">
          <div class="section-title">AI 辅助诊断结果</div>
          <div class="diag-grid">
            <div class="diag-item">
              <span class="diag-label">诊断结论：</span>
              <span class="diag-badge" :class="classificationClass">{{ result.classification }}</span>
            </div>
            <div class="diag-item" v-if="result.detection_score != null">
              <span class="diag-label">检测证据分：</span>
              <span class="diag-value">{{ result.detection_score.toFixed(3) }}</span>
            </div>
            <!-- 预后：由灌肠复位成功率推导，与诊断结论分栏呈现 -->
            <div class="diag-item" v-if="result.severity">
              <span class="diag-label">预 后 分 级：</span>
              <span class="severity-badge" :class="severityClass">{{ result.severity }}</span>
            </div>
            <div class="diag-item" v-if="result.treatment_success_rate != null">
              <span class="diag-label">治疗成功率：</span>
              <span class="diag-value">空气灌肠复位{{ (result.treatment_success_rate * 100).toFixed(0) }}%</span>
            </div>
          </div>
          <div class="model-trace-note">
            注：「检测证据分」是模型对本次影像中肠套叠相关特征的响应强度（非阳性概率，未经概率标定）；
            报告不给出"置信度百分比"——该数值由评估集的历史精度表换算而来，与本次病例无关。
            「预后分级」由复位成功率反推，不代表病灶本身的解剖严重程度。
          </div>
          <!-- 模型溯源：报告归档需能追溯是哪个模型/版本产出的结果 -->
          <div class="model-trace" v-if="modelTraceText">{{ modelTraceText }}</div>
        </div>

        <!-- 治疗建议 -->
        <div class="report-section" v-if="result?.treatment_advice">
          <div class="section-title">治疗建议</div>
          <div class="advice-box">{{ result.treatment_advice }}</div>
        </div>

        <!-- 声明 -->
        <div class="report-section">
          <div class="section-title">免责声明</div>
          <div class="disclaimer">
            1. 本报告由AI辅助生成，仅供临床参考，不作法律依据。<br>
            2. 请结合临床症状及其他检查结果综合判断。
          </div>
        </div>

        <!-- 签名区域 -->
        <div class="signature-area">
          <div class="signature-item">
            <span class="signature-label">报　告：</span>
            <span class="signature-line">_______________</span>
          </div>
          <div class="signature-item">
            <span class="signature-label">审　核：</span>
            <span class="signature-line">_______________</span>
          </div>
        </div>

        <!-- 底部固定栏 -->
        <div class="page-footer">
          <div class="footer-line"></div>
          <div class="footer-main">
            <div class="footer-left">
              <span>地址：芜湖市镜湖区赭山西路2号</span>
              <span class="footer-gap"></span>
              <span>电话：0553-5739114</span>
              <span>0553-5739184</span>
            </div>
            <div class="footer-page">1</div>
          </div>
          <div class="footer-disclaimer">此报告签章有效，仅供临床参考，不作法律依据。</div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, nextTick, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { useSettingsStore } from '../stores/settings'
import api from '../api/index'
import { formatDateTime } from '../utils/time'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  patient: { type: Object, default: null },
  result: { type: Object, default: null },
  imageUrl: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const settings = useSettingsStore()
const reportRef = ref(null)
const printing = ref(false)
const imageLoaded = ref(false)
const logoLoaded = ref(false)

const resolvedImageUrl = ref('')
let objectUrl = null

watch(() => props.imageUrl, async (newVal) => {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = null
  }
  resolvedImageUrl.value = ''
  
  if (!newVal) return
  
  if (newVal.startsWith('/api/')) {
    try {
      const requestUrl = newVal.replace(/^\/api/, '')
      const response = await api.get(requestUrl, { responseType: 'blob' })
      objectUrl = URL.createObjectURL(response.data)
      resolvedImageUrl.value = objectUrl
    } catch {
      resolvedImageUrl.value = ''
    }
  } else {
    resolvedImageUrl.value = newVal
  }
}, { immediate: true })

onUnmounted(() => {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
  }
})

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const examItem = '小儿腹部'
const todayIso = new Date().toISOString()
const examDate = computed(() => {
  return formatDateTime(props.result?.created_at || todayIso)
})
const reportDate = computed(() => {
  return formatDateTime(todayIso)
})

const classificationClass = computed(() => {
  const map = {
    '肠套叠阳性': 'badge-danger',
    '肠套叠阴性': 'badge-success',
    '图像质量不佳': 'badge-warning',
  }
  return map[props.result?.classification] || ''
})

const severityClass = computed(() => {
  const map = {
    '轻度': 'severity-mild',
    '中度': 'severity-moderate',
    '重度': 'severity-severe',
  }
  return map[props.result?.severity] || ''
})

// AI 实际产出的内容（判定 + 证据分 + 标注区域），**不含任何影像学征象描述**
const aiFindingHint = computed(() => {
  const r = props.result
  if (!r) return ''
  const score = r.detection_score != null ? `检测证据分 ${r.detection_score.toFixed(3)}` : '未记录检测证据分'
  const box = Array.isArray(r.roi_box) ? `，标注区域 (${r.roi_box.join(', ')})` : ''
  if (r.classification === '肠套叠阳性') {
    return `【AI 提示】本次 AI 在影像中识别到肠套叠相关特征（${score}${box}）。`
  }
  if (r.classification === '肠套叠阴性') {
    return `【AI 提示】本次 AI 未识别到肠套叠相关特征（${score}）。`
  }
  return `【AI 提示】本次影像未通过 AI 质量判定，未给出有效提示（${score}）；建议重新采集。`
})

// 模型溯源：优先分别展示 检测 / 分类 / 预后，旧数据回退到单一模型名
const modelTraceText = computed(() => {
  const r = props.result
  if (!r) return ''
  const parts = []
  if (r.detection_model_name) {
    parts.push(`检测模型：${r.detection_model_name}${r.detection_model_version ? ` v${r.detection_model_version}` : ''}`)
  }
  if (r.classification_model_name) {
    // 该槽位预留给「将来真正独立的诊断模型」；当前算法侧的判定步骤复用检测分数，
    // 折进「检测模型」一行，所以这里通常为空
    parts.push(`诊断模型：${r.classification_model_name}${r.classification_model_version ? ` v${r.classification_model_version}` : ''}`)
  }
  if (r.prognosis_model_name) {
    parts.push(`预后模型：${r.prognosis_model_name}${r.prognosis_model_version ? ` v${r.prognosis_model_version}` : ''}`)
  }
  if (!parts.length && r.model_name) {
    parts.push(`分析模型：${r.model_name}${r.model_version ? ` v${r.model_version}` : ''}`)
  }
  if (!parts.length) return ''
  let text = parts.join('　')
  if (r.inference_ms != null) text += `　（总耗时 ${r.inference_ms}ms）`
  return text
})

async function onPreviewOpened() {
  await settings.fetchSettings()
}

function waitForImages(container) {
  const imgs = container.querySelectorAll('img')
  const promises = []
  imgs.forEach((img) => {
    if (img.complete) return
    promises.push(
      new Promise((resolve) => {
        img.addEventListener('load', resolve, { once: true })
        img.addEventListener('error', resolve, { once: true })
      })
    )
  })
  return Promise.all(promises)
}

async function handlePrint() {
  if (!reportRef.value) return
  // 防护：没有检测结果时不生成空报告
  if (!props.result) {
    ElMessage.warning('未加载到检测结果，无法导出报告')
    return
  }
  printing.value = true
  try {
    await nextTick()
    const page = reportRef.value.querySelector('.report-page')
    await waitForImages(page)
    const canvas = await html2canvas(page, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
    })
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = pageWidth
    const imgHeight = (canvas.height * pageWidth) / canvas.width

    let heightLeft = imgHeight
    let position = 0
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight

    while (heightLeft > 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }

    const patientName = props.patient?.name || '报告'
    pdf.save(`${patientName}_超声检查报告.pdf`)
    ElMessage.success('PDF 导出成功')
  } catch (e) {
    console.error('PDF export error:', e)
    ElMessage.error('PDF 导出失败')
  } finally {
    printing.value = false
  }
}
</script>

<style scoped>
.print-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.no-result-tip {
  font-size: 13px;
  color: #b45309;
  background: #fff7e6;
  border: 1px solid #f2dfa6;
  border-radius: 6px;
  padding: 4px 10px;
}

.report-container {
  display: flex;
  justify-content: center;
}

.report-page {
  width: 210mm;
  min-height: 297mm;
  background: #fff;
  padding: 20mm 20mm 15mm 20mm;
  font-size: 14px;
  color: #000;
  line-height: 1.8;
  font-family: 'SimSun', 'STSong', 'FangSong', 'Noto Serif SC', serif;
  box-sizing: border-box;
  position: relative;
}

/* 医院页眉 */
.hospital-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 10px;
  padding-bottom: 10px;
}

.hospital-logo {
  flex-shrink: 0;
  width: 72px;
  height: 72px;
  object-fit: contain;
}

.hospital-brand {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.hospital-name-main {
  font-size: 26px;
  font-weight: 700;
  color: #006838;
  letter-spacing: 3px;
  font-family: 'SimHei', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
  text-align: center;
}

.hospital-name-main .name-part {
  margin-right: 6px;
}

.hospital-name-main .sub {
  font-size: 20px;
  color: #006838;
  font-weight: 700;
}

.hospital-name-main .sub2 {
  font-size: 20px;
  color: #006838;
  font-weight: 700;
}

.hospital-name-en {
  font-size: 10px;
  color: #006838;
  letter-spacing: 1px;
  font-family: 'Times New Roman', serif;
  text-align: center;
  opacity: 0.85;
}

.header-line {
  height: 1px;
  background: #000;
  margin: 10px 0 16px;
}

/* 报告标题 */
.report-title {
  font-size: 20px;
  font-weight: 700;
  color: #000;
  text-align: center;
  letter-spacing: 6px;
  margin-bottom: 20px;
  font-family: 'SimHei', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
}

/* 患者信息 */
.patient-info {
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  gap: 24px;
  margin-bottom: 4px;
}

.info-item {
  display: flex;
  align-items: baseline;
  min-width: 180px;
  flex: 1;
}

.info-item.wide {
  flex: 3;
}

.info-label {
  font-size: 14px;
  color: #333;
  font-weight: 600;
  white-space: pre;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
}

.info-value {
  font-size: 14px;
  color: #000;
  border-bottom: 1px solid #000;
  padding: 0 8px;
  min-width: 60px;
  flex: 1;
}

/* 报告区块 */
.report-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  color: #000;
  margin-bottom: 8px;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
}

.section-content p {
  margin: 0;
  text-indent: 2em;
  font-size: 14px;
}

.image-wrapper {
  text-align: center;
  padding: 8px;
  border: 1px solid #ccc;
  background: #fafafa;
}

.report-image {
  max-width: 100%;
  max-height: 280px;
  object-fit: contain;
}

/* 诊断结果网格 */
.diag-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 24px;
}

.diag-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.diag-label {
  font-size: 14px;
  color: #333;
  font-weight: 600;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
}

.diag-value {
  font-size: 14px;
  color: #000;
}

/* 模型溯源行（写在诊断结果下方，随报告一起打印） */
.model-trace {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed #bbb;
  font-size: 12px;
  color: #555;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
}

/* 术语说明（随报告打印，避免"证据分/预后分级"被误读） */
.model-trace-note {
  margin-top: 10px;
  font-size: 11px;
  line-height: 1.7;
  color: #777;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
}

.diag-note {
  font-size: 11px;
  color: #666;
}

/* 检查所见：AI 提示 + 待医生填写的空行 */
.ai-hint {
  margin: 0 0 6px;
  font-weight: 600;
  color: #000;
}
.finding-rule {
  margin: 0 0 10px;
  font-size: 11px;
  line-height: 1.7;
  color: #777;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
}
.finding-blank {
  margin: 6px 0 0;
  color: #333;
  letter-spacing: 1px;
  line-height: 2;
}

.diag-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 2px;
  font-weight: 600;
  font-size: 13px;
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.badge-danger {
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.badge-success {
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.badge-warning {
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.severity-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 2px;
  font-weight: 600;
  font-size: 13px;
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.severity-mild {
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.severity-moderate {
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.severity-severe {
  background: #fff;
  color: #000;
  border: 1px solid #000;
}

.advice-box {
  background: #f9f9f9;
  border: 1px solid #ccc;
  border-radius: 2px;
  padding: 10px 14px;
  color: #000;
  font-size: 14px;
  line-height: 1.8;
}

.disclaimer {
  color: #666;
  font-size: 13px;
  line-height: 1.8;
}

/* 签名区域 */
.signature-area {
  display: flex;
  justify-content: space-around;
  margin-top: 30px;
  margin-bottom: 20px;
  padding: 0 40px;
}

.signature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.signature-label {
  color: #333;
  font-weight: 600;
  font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
}

.signature-line {
  display: inline-block;
  min-width: 120px;
  border-bottom: 1px solid #000;
  height: 20px;
}

/* 页脚 */
.page-footer {
  margin-top: 20px;
  padding-top: 8px;
}

.footer-line {
  height: 1px;
  background: #000;
  margin-bottom: 6px;
}

.footer-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #333;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.footer-gap {
  display: inline-block;
  width: 16px;
}

.footer-page {
  font-size: 12px;
  color: #333;
  font-weight: 600;
}

.footer-disclaimer {
  font-size: 11px;
  color: #666;
  text-align: center;
  margin-top: 4px;
}
</style>
