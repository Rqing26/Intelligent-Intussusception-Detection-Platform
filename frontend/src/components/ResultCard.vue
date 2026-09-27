<template>
  <div class="result-card">
    <!-- 诊断分类大卡片 -->
    <div class="diag-hero" :class="heroClass">
      <div class="hero-icon">
        <el-icon :size="32">
          <CircleCheck v-if="result.classification === '肠套叠阴性'" />
          <WarningFilled v-else-if="result.classification === '肠套叠阳性'" />
          <Picture v-else />
        </el-icon>
      </div>
      <div class="hero-body">
        <div class="hero-label">诊断分类</div>
        <div class="hero-value">{{ result.classification }}</div>
      </div>
    </div>

    <!-- 置信度 -->
    <div class="result-section">
      <div class="section-header">
        <span class="section-label">置信度</span>
        <span class="section-value" :style="{ color: progressColor }">{{ confidencePercent }}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: confidencePercent + '%', background: progressColor }"></div>
      </div>
    </div>

    <!-- 分类概率分布 -->
    <div v-if="probList.length" class="result-section">
      <div class="section-header">
        <span class="section-label">分类概率</span>
      </div>
      <div class="prob-list">
        <div v-for="p in probList" :key="p.label" class="prob-item">
          <span class="prob-label">{{ p.label }}</span>
          <div class="prob-track">
            <div class="prob-fill" :style="{ width: p.percent + '%', background: p.color }"></div>
          </div>
          <span class="prob-value">{{ p.percent.toFixed(1) }}%</span>
        </div>
      </div>
    </div>

    <!-- 诊断等级 -->
    <div v-if="result.severity" class="result-section">
      <div class="section-header">
        <span class="section-label">诊断等级</span>
        <span class="severity-pill" :class="severityClass">{{ result.severity }}</span>
      </div>
    </div>

    <!-- 治疗成功率 -->
    <div v-if="result.severity" class="result-section rate-section">
      <div class="rate-header">
        <div class="rate-title">
          <el-icon :size="18"><FirstAidKit /></el-icon>
          治疗成功率
        </div>
        <div class="rate-value" :style="{ color: rateColor }">{{ (result.treatment_success_rate * 100).toFixed(0) }}%</div>
      </div>
      <div class="progress-track large">
        <div
          class="progress-fill"
          :style="{ width: Math.round(result.treatment_success_rate * 100) + '%', background: rateColor }"></div>
      </div>
      <p class="rate-desc">灌肠复位成功率预测</p>
    </div>

    <!-- 治疗建议 -->
    <div v-if="result.treatment_advice" class="result-section advice-section">
      <div class="advice-header">
        <el-icon :size="18"><InfoFilled /></el-icon>
        治疗建议
      </div>
      <div class="advice-body">{{ result.treatment_advice }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { CircleCheck, WarningFilled, Picture, FirstAidKit, InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  result: { type: Object, required: true },
})

const heroClass = computed(() => {
  const map = {
    '肠套叠阳性': 'hero-danger',
    '肠套叠阴性': 'hero-success',
    '图像质量不佳': 'hero-warning',
  }
  return map[props.result.classification] || 'hero-default'
})

const severityClass = computed(() => {
  const map = {
    '轻度': 'pill-success',
    '中度': 'pill-warning',
    '重度': 'pill-danger',
  }
  return map[props.result.severity] || 'pill-default'
})

const confidencePercent = computed(() => {
  const val = props.result.confidence
  if (val === null || val === undefined) return 0
  return Math.round(val * 100)
})

const LABEL_MAP = {
  '肠套叠阳性': '阳性',
  '肠套叠阴性': '阴性',
  '图像质量不佳': '质量不佳',
}
const COLOR_MAP = {
  '肠套叠阳性': 'var(--danger)',
  '肠套叠阴性': 'var(--success)',
  '图像质量不佳': 'var(--warning)',
}
const probList = computed(() => {
  const probs = props.result.class_probabilities
  if (!probs || typeof probs !== 'object') return []
  return Object.entries(probs).map(([label, val]) => ({
    label: LABEL_MAP[label] || label,
    percent: (Number(val) || 0) * 100,
    color: COLOR_MAP[label] || 'var(--primary)',
  }))
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
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 诊断大卡片 */
.diag-hero {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 20px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}
.diag-hero.hero-success {
  background: var(--bg-tag-success);
  border-color: var(--border-color);
}
.diag-hero.hero-danger {
  background: var(--bg-tag-danger);
  border-color: var(--border-color);
}
.diag-hero.hero-warning {
  background: var(--bg-tag-warning);
  border-color: var(--border-color);
}
.diag-hero.hero-default {
  background: var(--bg-tag-info);
  border-color: var(--border-color);
}

.hero-icon {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.hero-success .hero-icon { color: var(--success); }
.hero-danger .hero-icon { color: var(--danger); }
.hero-warning .hero-icon { color: var(--warning); }
.hero-default .hero-icon { color: var(--primary); }

.hero-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  margin-bottom: 4px;
  letter-spacing: 0.04em;
}
.hero-value {
  font-family: var(--font-display);
  font-size: 23px;
  font-weight: 650;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

/* 通用 section */
.result-section {
  padding: 0 4px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.section-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.04em;
}
.section-value {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
}

/* 进度条 */
.progress-track {
  height: 6px;
  background: var(--border-light);
  border-radius: 4px;
  overflow: hidden;
}
.progress-track.large {
  height: 10px;
  border-radius: 5px;
}
.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}
.progress-track.large .progress-fill {
  border-radius: 5px;
}

/* 分类概率列表 */
.prob-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.prob-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.prob-label {
  width: 60px;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
  text-align: right;
  flex-shrink: 0;
}
.prob-track {
  flex: 1;
  height: 6px;
  background: var(--border-light);
  border-radius: 3px;
  overflow: hidden;
}
.prob-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.prob-value {
  width: 48px;
  font-size: 12px;
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--text-primary);
  text-align: right;
  flex-shrink: 0;
}

/* 等级 pill */
.severity-pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
}
.pill-success { background: var(--bg-tag-success); color: var(--success); }
.pill-warning { background: var(--bg-tag-warning); color: var(--warning); }
.pill-danger { background: var(--bg-tag-danger); color: var(--danger); }
.pill-default { background: var(--bg-tag-info); color: var(--primary); }

/* 治疗成功率 */
.rate-section {
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
}
.rate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.rate-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.rate-value {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
}
.rate-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin: 8px 0 0;
}

/* 治疗建议 */
.advice-section {
  background: var(--bg-advice);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 20px;
}
.advice-header {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--warning);
  margin-bottom: 10px;
}
.advice-body {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.8;
  font-weight: 500;
}
</style>
