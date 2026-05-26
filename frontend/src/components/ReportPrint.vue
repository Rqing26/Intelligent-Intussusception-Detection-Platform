<template>
  <el-dialog
    v-model="visible"
    title="打印预览"
    width="840px"
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
        <div class="report-header">
          <div class="hospital-name-cn">{{ settings.hospitalName }}</div>
          <div class="hospital-name-en">{{ settings.hospitalNameEn }}</div>
          <div class="header-divider"></div>
          <div class="report-title">彩色多普勒超声检查报告</div>
        </div>

        <table class="info-table">
          <colgroup>
            <col style="width:15%" />
            <col style="width:35%" />
            <col style="width:15%" />
            <col style="width:35%" />
          </colgroup>
          <tr>
            <td class="info-label">姓名</td>
            <td>{{ patient?.name || '-' }}</td>
            <td class="info-label">性别</td>
            <td>{{ patient?.gender || '-' }}</td>
          </tr>
          <tr>
            <td class="info-label">年龄(月)</td>
            <td>{{ patient?.age || '-' }}</td>
            <td class="info-label">病历号</td>
            <td>{{ patient?.medical_record_no || '-' }}</td>
          </tr>
          <tr>
            <td class="info-label">检查项目</td>
            <td>{{ examItem }}</td>
            <td class="info-label">检查日期</td>
            <td>{{ examDate }}</td>
          </tr>
          <tr>
            <td class="info-label">临床症状</td>
            <td colspan="3">{{ patient?.clinical_symptoms || '-' }}</td>
          </tr>
          <tr>
            <td class="info-label">超声系统</td>
            <td>IVSP-2</td>
            <td class="info-label">报告日期</td>
            <td>{{ reportDate }}</td>
          </tr>
        </table>

        <div class="report-section" v-if="result">
          <div class="section-title">检查所见</div>
          <div class="section-content">
            <p>超声所见：{{ resultDescription }}</p>
          </div>
        </div>

        <div class="report-section" v-if="imageUrl">
          <div class="section-title">超声影像</div>
          <div class="image-wrapper">
            <img :src="imageUrl" alt="超声影像" class="report-image" @load="imageLoaded = true" />
          </div>
        </div>

        <div class="report-section" v-if="result">
          <div class="section-title">AI 辅助诊断结果</div>
          <table class="diag-table">
            <tr>
              <td class="info-label">诊断分类</td>
              <td>
                <span class="diag-badge" :class="classificationClass">
                  {{ result.classification }}
                </span>
              </td>
              <td class="info-label">置信度</td>
              <td>{{ confidencePercent }}%</td>
            </tr>
            <tr v-if="result.severity">
              <td class="info-label">诊断等级</td>
              <td>
                <span class="severity-badge" :class="severityClass">
                  {{ result.severity }}
                </span>
              </td>
              <td class="info-label">治疗成功率</td>
              <td>
                <span v-if="result.treatment_success_rate != null">
                  灌肠成功率{{ (result.treatment_success_rate * 100).toFixed(0) }}%
                </span>
                <span v-else>-</span>
              </td>
            </tr>
          </table>
        </div>

        <div class="report-section" v-if="result?.treatment_advice">
          <div class="section-title">治疗建议</div>
          <div class="advice-box">{{ result.treatment_advice }}</div>
        </div>

        <div class="report-section">
          <div class="section-title">声明</div>
          <div class="disclaimer">
            本报告由AI辅助生成，仅供临床参考，不具备法律效力。请结合临床症状及其他检查结果综合判断。
          </div>
        </div>

        <div class="signature-area">
          <div class="signature-item">
            <div class="signature-label">报告医生：_______________</div>
          </div>
          <div class="signature-item">
            <div class="signature-label">审核医生：_______________</div>
          </div>
        </div>

        <div class="report-footer">
          <div class="footer-divider"></div>
          <div class="footer-info">
            <span>{{ settings.hospitalAddress }}</span>
            <span class="footer-sep">|</span>
            <span>电话：{{ settings.hospitalPhone }}</span>
          </div>
          <div class="footer-disclaimer">* 医生签名有效，仅供临床参考，不具备法律效力 *</div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
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
  width: 720px;
  background: #fff;
  padding: 36px 40px;
  font-size: 13px;
  color: #1e293b;
  line-height: 1.7;
  border: 1px solid #e2e8f0;
}

.report-header {
  text-align: center;
  margin-bottom: 20px;
}

.hospital-name-cn {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 2px;
}

.hospital-name-en {
  font-size: 10px;
  color: #64748b;
  letter-spacing: 0.5px;
  margin-top: 2px;
}

.header-divider {
  height: 2px;
  background: #1e293b;
  margin: 12px auto;
  width: 80%;
}

.report-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: 4px;
  margin-top: 8px;
}

.info-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}

.info-table td {
  border: 1px solid #cbd5e1;
  padding: 5px 8px;
}

.info-label {
  background: #f1f5f9;
  font-weight: 600;
  color: #334155;
}

.report-section {
  margin-bottom: 14px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  border-left: 3px solid #1e293b;
  padding-left: 8px;
  margin-bottom: 8px;
}

.section-content p {
  margin: 0;
  text-indent: 2em;
}

.image-wrapper {
  text-align: center;
  padding: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  background: #f8fafc;
}

.report-image {
  max-width: 100%;
  max-height: 320px;
  object-fit: contain;
}

.diag-table {
  width: 100%;
  border-collapse: collapse;
}

.diag-table td {
  border: 1px solid #cbd5e1;
  padding: 5px 8px;
}

.diag-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 3px;
  font-weight: 600;
  font-size: 12px;
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
  border-radius: 3px;
  font-weight: 600;
  font-size: 12px;
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
  border-radius: 4px;
  padding: 10px 14px;
  color: #78350f;
}

.disclaimer {
  color: #94a3b8;
  font-size: 12px;
}

.signature-area {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
  margin-bottom: 20px;
  padding: 0 20px;
}

.signature-item {
  text-align: center;
}

.signature-label {
  font-size: 13px;
  color: #475569;
}

.report-footer {
  text-align: center;
}

.footer-divider {
  height: 1px;
  background: #cbd5e1;
  margin-bottom: 8px;
}

.footer-info {
  font-size: 11px;
  color: #64748b;
}

.footer-sep {
  margin: 0 8px;
}

.footer-disclaimer {
  font-size: 10px;
  color: #94a3b8;
  margin-top: 2px;
}
</style>
