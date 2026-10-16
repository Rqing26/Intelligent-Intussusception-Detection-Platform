<template>
  <el-dialog
    :model-value="visible"
    :title="`手动裁剪 · ${fileName || ''}`"
    width="min(860px, 94vw)"
    :close-on-click-modal="false"
    :close-on-press-escape="!submitting"
    append-to-body
    destroy-on-close
    @update:model-value="onVisibleChange"
  >
    <div class="crop-dialog-body">
      <div class="crop-stage-wrap">
        <div v-if="!imgSrc" class="crop-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>影像加载中...</span>
        </div>
        <div
          v-show="imgSrc"
          ref="stageRef"
          class="crop-stage"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointerleave="onPointerUp"
        >
          <img
            ref="imgRef"
            :src="imgSrc"
            class="crop-img"
            alt="待裁剪影像"
            draggable="false"
            @load="onImageLoad"
          />
          <!-- 四周半透明遮罩 + 保留区挖空：直观呈现「裁掉的是什么」 -->
          <div v-if="sel" class="crop-mask" :style="maskStyle" />
          <div v-if="sel" class="crop-rect" :style="rectStyle">
            <span class="crop-rect-size">{{ Math.round(sel.w / scale) }} × {{ Math.round(sel.h / scale) }} px</span>
            <i class="crop-handle crop-handle-tl" /><i class="crop-handle crop-handle-tr" />
            <i class="crop-handle crop-handle-bl" /><i class="crop-handle crop-handle-br" />
          </div>
          <div v-if="!sel && imgSrc" class="crop-hint">在影像上按住拖动，框选要保留的超声图像区</div>
        </div>
      </div>

      <div class="crop-tips">
        <el-icon><InfoFilled /></el-icon>
        <div>
          框外的区域（患者信息条、参数栏、深度刻度条等）将在确认后<b>永久去除</b>，只保留框内内容用于 AI 检测。
          重新拖动可调整框；每张影像裁剪一次，确认前请核对。
        </div>
      </div>
    </div>

    <template #footer>
      <div class="crop-footer">
        <span class="crop-footer-info">{{ footerInfo }}</span>
        <div>
          <el-button :disabled="submitting" @click="onSkip">跳过本张（不裁剪）</el-button>
          <el-button
            type="primary"
            :disabled="!canSubmit"
            :loading="submitting"
            @click="onConfirm"
          >确认裁剪</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * 手动裁剪对话框（去标识）
 * ---------------------------------------------------------
 * 在已上传的影像上拖动框选「要保留的超声图像区」，确认后把
 * 框（原图像素坐标 [x0, y0, x1, y1]）交给父组件去调裁剪接口。
 *
 * - 影像通过 axios 以 blob 加载（带 JWT），转 objectURL 展示；
 * - 坐标换算：显示坐标 × (naturalWidth / 显示宽度) = 原图像素坐标；
 * - 每次拖动都是重画（不做拖动/缩放微调，超声整帧裁剪一次到位即可）。
 */
import { ref, computed, watch, onUnmounted } from 'vue'
import { Loading, InfoFilled } from '@element-plus/icons-vue'
import api from '../api/index'

const props = defineProps({
  visible: { type: Boolean, default: false },
  imageId: { type: [Number, String], default: null },
  fileName: { type: String, default: '' },
})
const emit = defineEmits(['confirm', 'cancel'])

const imgSrc = ref('')
const stageRef = ref(null)
const imgRef = ref(null)
const submitting = ref(false)
// 选区（显示坐标）与缩放比（显示 → 原图）
const sel = ref(null)          // {x, y, w, h}，显示像素
const scale = ref(1)           // 显示尺寸 / 原始尺寸
let objectUrl = null
let dragging = false
let dragStart = null

const canSubmit = computed(() =>
  !!sel.value && sel.value.w >= 8 && sel.value.h >= 8 && !submitting.value)

const footerInfo = computed(() => {
  if (!sel.value) return '尚未框选保留区'
  const w = Math.round(sel.value.w / scale.value)
  const h = Math.round(sel.value.h / scale.value)
  return `已选保留区：约 ${w} × ${h} 像素`
})

const rectStyle = computed(() => sel.value && ({
  left: `${sel.value.x}px`, top: `${sel.value.y}px`,
  width: `${sel.value.w}px`, height: `${sel.value.h}px`,
}))
// 用巨大的 box-shadow 做四周遮罩：保留区被 rect 盖住不受影响
const maskStyle = computed(() => sel.value && ({
  left: `${sel.value.x}px`, top: `${sel.value.y}px`,
  width: `${sel.value.w}px`, height: `${sel.value.h}px`,
  'box-shadow': '0 0 0 9999px rgba(15, 26, 32, 0.55)',
}))

watch(() => props.visible, async (v) => {
  if (!v) return
  sel.value = null
  dragging = false
  await loadImage()
})

async function loadImage() {
  imgSrc.value = ''
  if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = null }
  if (!props.imageId) return
  try {
    const res = await api.get(`/images/${props.imageId}`, { responseType: 'blob' })
    objectUrl = URL.createObjectURL(res.data)
    imgSrc.value = objectUrl
  } catch (e) {
    imgSrc.value = ''
  }
}

function onImageLoad() {
  const img = imgRef.value
  if (!img) return
  scale.value = img.clientWidth > 0 ? img.naturalWidth / img.clientWidth : 1
}

function stagePoint(e) {
  const rect = stageRef.value.getBoundingClientRect()
  return {
    x: Math.max(0, Math.min(e.clientX - rect.left, rect.width)),
    y: Math.max(0, Math.min(e.clientY - rect.top, rect.height)),
  }
}

function onPointerDown(e) {
  if (e.button !== 0 || !imgSrc.value) return
  dragging = true
  dragStart = stagePoint(e)
  sel.value = { x: dragStart.x, y: dragStart.y, w: 0, h: 0 }
  e.target.setPointerCapture?.(e.pointerId)
}

function onPointerMove(e) {
  if (!dragging) return
  const p = stagePoint(e)
  sel.value = {
    x: Math.min(dragStart.x, p.x),
    y: Math.min(dragStart.y, p.y),
    w: Math.abs(p.x - dragStart.x),
    h: Math.abs(p.y - dragStart.y),
  }
}

function onPointerUp() {
  dragging = false
}

function onConfirm() {
  if (!canSubmit.value) return
  submitting.value = true
  // 显示坐标 → 原图像素坐标（取整、夹到图内）
  const x0 = Math.max(0, Math.round(sel.value.x * scale.value))
  const y0 = Math.max(0, Math.round(sel.value.y * scale.value))
  const x1 = Math.round((sel.value.x + sel.value.w) * scale.value)
  const y1 = Math.round((sel.value.y + sel.value.h) * scale.value)
  emit('confirm', [x0, y0, x1, y1])
  // 父组件负责关对话框与错误提示；这里复位提交态交由 visible 变化处理
  submitting.value = false
}

function onSkip() {
  sel.value = null
  emit('cancel')
}

function onVisibleChange(v) {
  if (!v) emit('cancel')
}

onUnmounted(() => {
  if (objectUrl) URL.revokeObjectURL(objectUrl)
})
</script>

<style scoped>
.crop-dialog-body { display: flex; flex-direction: column; gap: 14px; }
.crop-stage-wrap {
  display: flex;
  justify-content: center;
  background: var(--bg-detail-item, #f5f7f8);
  border: 1px solid var(--border-color, #e4e7ed);
  border-radius: 10px;
  padding: 12px;
  min-height: 280px;
}
.crop-loading {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; color: var(--text-muted, #909399); font-size: 13px; padding: 80px 0;
}
.crop-loading .is-loading { font-size: 30px; }
.crop-stage {
  position: relative;
  display: inline-flex;
  max-width: 100%;
  cursor: crosshair;
  touch-action: none;
  user-select: none;
  -webkit-user-drag: none;
}
.crop-img {
  max-width: 100%;
  max-height: 58vh;
  width: auto; height: auto;
  display: block;
  pointer-events: none;      /* 拖拽事件全部走 stage，避免 img 拦截 */
}
.crop-mask {
  position: absolute;
  pointer-events: none;
}
.crop-rect {
  position: absolute;
  border: 2px solid #409eff;
  border-radius: 2px;
  pointer-events: none;
  box-sizing: border-box;
}
.crop-rect-size {
  position: absolute;
  top: -24px; left: 0;
  font-size: 11px;
  line-height: 18px;
  padding: 0 8px;
  color: #fff;
  background: #409eff;
  border-radius: 4px;
  white-space: nowrap;
}
.crop-handle {
  position: absolute;
  width: 10px; height: 10px;
  background: #fff;
  border: 2px solid #409eff;
  border-radius: 2px;
}
.crop-handle-tl { top: -6px; left: -6px; }
.crop-handle-tr { top: -6px; right: -6px; }
.crop-handle-bl { bottom: -6px; left: -6px; }
.crop-handle-br { bottom: -6px; right: -6px; }
.crop-hint {
  position: absolute;
  left: 50%; top: 50%;
  transform: translate(-50%, -50%);
  padding: 8px 16px;
  font-size: 13px;
  color: #fff;
  background: rgba(15, 26, 32, 0.62);
  border-radius: 8px;
  pointer-events: none;
  white-space: nowrap;
}
.crop-tips {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.7;
  color: var(--text-muted, #909399);
  background: var(--bg-page, #f5f7f8);
  border-radius: 8px;
  padding: 10px 12px;
}
.crop-tips .el-icon { color: #409eff; flex-shrink: 0; margin-top: 2px; }
.crop-footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.crop-footer-info { font-size: 12px; color: var(--text-muted, #909399); }
@media (max-width: 760px) {
  .crop-footer { flex-direction: column; align-items: stretch; }
  .crop-footer-info { order: 2; text-align: center; }
}
</style>
