<template>
  <div class="result-card">
    <div class="result-section">
      <span class="result-label">诊断结果</span>
      <el-tag
        size="large"
        effect="dark"
        :type="tagType"
        class="result-tag"
      >
        {{ result.classification }}
      </el-tag>
    </div>

    <div class="result-section">
      <span class="result-label">置信度</span>
      <el-progress
        :percentage="confidencePercent"
        :stroke-width="16"
        :color="progressColor"
      />
    </div>

    <div v-if="result.treatment_advice" class="result-section">
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

const tagType = computed(() => {
  const map = {
    '肠套叠阳性': 'danger',
    '肠套叠阴性': 'success',
    '图像质量不佳': 'warning',
  }
  return map[props.result.classification] || 'info'
})

const confidencePercent = computed(() => {
  const val = props.result.confidence
  if (val === null || val === undefined) return 0
  return Math.round(val * 100)
})

const progressColor = computed(() => {
  const val = props.result.confidence
  if (val >= 0.9) return '#67c23a'
  if (val >= 0.75) return '#e6a23c'
  return '#f56c6c'
})
</script>

<style scoped>
.result-card {
  padding: 20px;
}

.result-section {
  margin-bottom: 24px;
}

.result-label {
  display: block;
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.result-tag {
  font-size: 16px;
}

.advice-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 14px 16px;
}

.advice-icon {
  font-size: 20px;
  color: #e6a23c;
  flex-shrink: 0;
  margin-top: 1px;
}

.advice-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}
</style>
