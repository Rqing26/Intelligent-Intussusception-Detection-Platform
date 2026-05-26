<template>
  <el-dialog
    v-model="visible"
    title="打印预览"
    width="900px"
    append-to-body
    @opened="onPreviewOpened"
  >
    <div class="print-actions">
      <el-button type="primary" @click="handlePrint" :loading="printing">
        <el-icon><Printer /></el-icon>导出PDF
      </el-button>
      <el-button @click="visible = false">关闭</el-button>
    </div>

    <div ref="reportRef" class="report-container" v-loading="printing">
      <div class="report-page">
        <!-- 医院页眉 -->
        <div class="hospital-header">
          <div class="hospital-logo">
            <div class="logo-circle">
              <span class="logo-cross">+</span>
            </div>
          </div>
          <div class="hospital-brand">
            <div class="hospital-name-main">
              <span class="name-part">皖南医学院</span>
              <span class="name-part highlight">第一附属医院</span>
              <span class="name-part sub">弋矶山医院</span>
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
              <span class="info-label">申请科室：</span>
              <span class="info-value">小儿外科</span>
            </div>
            <div class="info-item">
              <span class="info-label">病 历 号：</span>
              <span class="info-value">{{ patient?.medical_record_no || '-' }}</span>
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
        <div class="report-section" v-if="result">
          <div class="section-title">检查所见</div>
          <div class="section-content">
            <p>超声所见：{{ resultDescription }}</p>
          </div>
        </div>

        <!-- 超声影像 -->
        <div class="report-section" v-if="imageUrl">
          <div class="section-title">超声影像</div>
          <div class="image-wrapper">
            <img :src="imageUrl" alt="超声影像" class="report-image" @load="imageLoaded = true" />
          </div>
        </div>

        <!-- AI 辅助诊断结果 -->
        <div class="report-section" v-if="result">
          <div class="section-title">AI 辅助诊断结果</div>
          <div class="diag-grid">
            <div class="diag-item">
              <span class="diag-label">诊断分类：</span>
              <span class="diag-badge" :class="classificationClass">{{ result.classification }}</span>
            </div>
            <div class="diag-item">
              <span class="diag-label">置 信 度：</span>
              <span class="diag-value">{{ confidencePercent }}%</span>
            </div>
            <div class="diag-item" v-if="result.severity">
              <span class="diag-label">诊断等级：</span>
              <span class="severity-badge" :class="severityClass">{{ result.severity }}</span>
            </div>
            <div class="diag-item" v-if="result.treatment_success_rate != null">
              <span class="diag-label">治疗成功率：</span>
              <span class="diag-value">灌肠成功率{{ (result.treatment_success_rate * 100).toFixed(0) }}%</span>
            </div>
          </div>
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
import { ref, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { useSettingsStore } from '../stores/settings'

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

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const examItem = '小儿腹部'
const examDate = computed(() => {
  if (props.result?.created_at) return formatDate(props.result.created_at)
  return formatDate(new Date().toISOString())
})
const reportDate = computed(() => {
  return formatDate(new Date().toISOString())
})

const confidencePercent = computed(() => {
  const v = props.result?.confidence
  if (v == null) return 0
  return Math.round(v * 100)
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

const resultDescription = computed(() => {
  if (!props.result) return ''
  const cls = props.result.classification
  if (cls === '肠套叠阳性') return '超声检查显示肠套叠典型"同心圆征"及"套筒征"，套叠部位可见多层肠壁结构，CDFI显示套叠肠壁血流信号。'
  if (cls === '肠套叠阴性') return '超声检查未见明确肠套叠征象，肠壁结构清晰，未见"同心圆征"及"套筒征"，CDFI显示肠壁血流信号正常。'
  return '图像质量欠佳，无法满足诊断要求，建议重新采集超声影像。'
})

function formatDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

async function onPreviewOpened() {
  await settings.fetchSettings()
}

async function handlePrint() {
  if (!reportRef.value) return
  printing.value = true
  try {
    await nextTick()
    const canvas = await html2canvas(reportRef.value.querySelector('.report-page'), {
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
  margin-bottom: 16px;
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
  gap: 16px;
  margin-bottom: 8px;
}

.hospital-logo {
  flex-shrink: 0;
}

.logo-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 2px solid #2d8c3f;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.logo-cross {
  font-size: 28px;
  font-weight: 700;
  color: #2d8c3f;
  font-family: 'Times New Roman', serif;
}

.hospital-brand {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hospital-name-main {
  font-size: 22px;
  font-weight: 700;
  color: #2d8c3f;
  letter-spacing: 2px;
  font-family: 'SimHei', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
}

.hospital-name-main .name-part {
  margin-right: 4px;
}

.hospital-name-main .highlight {
  color: #2d8c3f;
}

.hospital-name-main .sub {
  font-size: 18px;
  color: #2d8c3f;
}

.hospital-name-en {
  font-size: 10px;
  color: #666;
  letter-spacing: 0.5px;
  font-family: 'Times New Roman', serif;
}

.header-line {
  height: 1px;
  background: #2d8c3f;
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

.diag-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 2px;
  font-weight: 600;
  font-size: 13px;
}

.badge-danger {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.badge-success {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.badge-warning {
  background: #fffbeb;
  color: #d97706;
  border: 1px solid #fde68a;
}

.severity-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 2px;
  font-weight: 600;
  font-size: 13px;
}

.severity-mild {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}

.severity-moderate {
  background: #fefce8;
  color: #ca8a04;
  border: 1px solid #fef08a;
}

.severity-severe {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.advice-box {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 2px;
  padding: 10px 14px;
  color: #78350f;
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
