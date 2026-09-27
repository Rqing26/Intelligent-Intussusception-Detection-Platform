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

    <!-- 检测证据分（主位）：模型真正有区分度的输出。
         原来的「置信度 %」与「分类概率条」已撤掉，原因见下方 script 里的说明。 -->
    <div class="result-section">
      <div class="section-header">
        <span class="section-label">
          检测证据分
          <el-tooltip placement="top" effect="dark">
            <template #content>
              <div style="max-width: 320px; line-height: 1.7">
                模型对「这张图存在肠套叠病灶」的<b>原始证据强度</b>（未标定，0~1）<br>
                数值越高证据越强，但<b>不是"阳性概率"</b>（判界阈值仅 0.0145）<br>
                本平台实测参考：真实超声约 0.76~0.91，随机噪声约 0.27，非医学图像 &lt;0.02
              </div>
            </template>
            <el-icon class="label-help"><QuestionFilled /></el-icon>
          </el-tooltip>
        </span>
        <span class="section-value evidence-value">
          {{ result.detection_score != null ? result.detection_score.toFixed(3) : '—' }}
        </span>
      </div>
      <div class="progress-track">
        <div
          class="progress-fill evidence-fill"
          :style="{ width: (result.detection_score != null ? result.detection_score * 100 : 0) + '%' }"
        ></div>
      </div>
      <p class="score-note" v-if="result.detection_score == null">
        该结果未记录证据分（旧数据或 Mock 结果）
      </p>
    </div>

    <!-- 分类概率分布：**故意不展示**。
         算法侧给出的 class_probabilities 是用标定表从证据分换算的（阳性 0.99 / 阴性 0.01），
         在证据分 ≥0.75 后恒定，既不随本次病例变化，也不是模型概率输出；
         展示成"概率条"会被读成"阳性概率 99.2%"，与"只留证据分"的口径冲突。
         需要概率条时应由算法侧提供**真正标定过**的概率。 -->

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
import { CircleCheck, WarningFilled, Picture, FirstAidKit, InfoFilled, QuestionFilled } from '@element-plus/icons-vue'

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

// ⚠️ 2026-09-27：本组件**不再展示「置信度百分比」与「分类概率条」**。
// 原因（实测，见 backend/tools/eval_confidence.py 与 docs/准确率与置信度核实.md）：
//   · 那两个数都不是模型输出，而是用评估集标定表把「证据分」换算出来的查表值；
//   · 它在证据分 ≥0.75 后恒为 99.2%（阴性侧 0.8%），对本次结果零区分度，
//     展示成百分比 / 概率条会被读成"这个病人阳性概率 99.2%"；
//   · 现在只呈现模型真正的输出：诊断结论 + 检测证据分（见模板里的「检测证据分」区块）。
//   · 后端 confidence / class_probabilities 字段与落库**没有动**（契约字段仍在），
//     医学与统计口径的事不该由前端擅改。
// 需要概率条时，应由算法侧提供**真正标定过**的概率。

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

/* 证据分用中性主色：它不代表好坏，只代表证据强度 */
.evidence-value {
  color: var(--primary);
}
.evidence-fill {
  background: var(--primary);
}
/* 标签旁的说明图标 */
.label-help {
  margin-left: 4px;
  color: var(--text-muted);
  cursor: help;
  vertical-align: -2px;
}
/* 证据分缺失时的补充说明 */
.score-note {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--text-muted);
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
