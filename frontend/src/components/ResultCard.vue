<template>
  <div class="result-card">
    <div class="result-section">
      <span class="result-label">诊断分类</span>
      <span :class="['seal-tag', classificationClass]">
        {{ result.classification }}
      </span>
    </div>

    <div class="result-section">
      <span class="result-label">置信度</span>
      <div class="progress-wrap">
        <div class="progress-track">
          <div
            class="progress-fill"
            :style="{ width: confidencePercent + '%', background: progressColor }"
          />
        </div>
        <span class="progress-text">{{ confidencePercent }}%</span>
      </div>
    </div>

    <div v-if="result.severity" class="result-section">
      <span class="result-label">诊断等级</span>
      <span :class="['seal-tag', severityClass]">
        {{ result.severity }}
      </span>
    </div>

    <div v-if="result.severity" class="result-section highlight">
      <span class="result-label">治疗成功率</span>
      <div class="success-rate-box">
        <div class="success-rate-main">
          <span class="success-rate-value" :style="{ color: rateColor }">{{ (result.treatment_success_rate * 100).toFixed(0) }}%</span>
          <span class="success-rate-desc">灌肠成功率</span>
        </div>
        <div class="progress-track large">
          <div
            class="progress-fill"
            :style="{ width: Math.round(result.treatment_success_rate * 100) + '%', background: rateColor }"
          />
        </div>
      </div>
    </div>

    <div v-if="result.treatment_advice" class="result-section highlight">
      <span class="result-label">治疗建议</span>
      <div class="advice-card">
        <el-icon class="advice-icon"><WarningFilled /></el-icon>
        <span class="advice-text">{{ result.treatment_advice }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true,
  },
})

const classificationClass = computed(() => {
  const map = {
    '肠套叠阳性': 'seal-vermillion',
    '肠套叠阴性': 'seal-malachite',
    '图像质量不佳': 'seal-gold',
  }
  return map[props.result.classification] || 'seal-ink'
})

const severityClass = computed(() => {
  const map = {
    '轻度': 'seal-malachite',
    '中度': 'seal-gold',
    '重度': 'seal-vermillion',
  }
  return map[props.result.severity] || 'seal-ink'
})

const confidencePercent = computed(() => {
  const val = props.result.confidence
  if (val === null || val === undefined) return 0
  return Math.round(val * 100)
})

const progressColor = computed(() => {
  const val = props.result.confidence
  if (val >= 0.9) return 'var(--success)'
  if (val >= 0.75) return 'var(--warning)'
  return 'var(--danger)'
})

const rateColor = computed(() => {
  const rate = props.result.treatment_success_rate
  if (rate >= 0.9) return 'var(--success)'
  if (rate >= 0.8) return 'var(--warning)'
  return 'var(--danger)'
})
</script>

<style scoped>
.result-card {
  padding: 4px;
}

.result-section {
  margin-bottom: 22px;
}
.result-section:last-child {
  margin-bottom: 0;
}
.result-section.highlight {
  background: var(--bg-detail-item);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  margin-left: -4px;
  margin-right: -4px;
}

.result-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 8px;
  font-family: var(--font-display);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.seal-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 2px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  border: 1px solid;
}
.seal-vermillion { background: var(--bg-tag-danger); color: var(--danger); border-color: rgba(139, 38, 53, 0.3); }
.seal-malachite { background: var(--bg-tag-success); color: var(--success); border-color: rgba(45, 90, 63, 0.3); }
.seal-gold { background: var(--bg-tag-warning); color: var(--warning); border-color: rgba(166, 93, 58, 0.3); }
.seal-ink { background: rgba(44, 36, 27, 0.06); color: var(--text-secondary); border-color: rgba(44, 36, 27, 0.2); }

.progress-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}
.progress-track {
  flex: 1;
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}
.progress-track.large {
  height: 12px;
  border-radius: 6px;
}
.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}
.progress-text {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  min-width: 90px;
  text-align: right;
}

.success-rate-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.success-rate-main {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.success-rate-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}
.success-rate-desc {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 600;
}

.advice-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 4px 2px;
}
.advice-icon {
  font-size: 22px;
  color: var(--warning);
  flex-shrink: 0;
  margin-top: 2px;
}
.advice-text {
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.7;
  font-weight: 600;
}
</style>
