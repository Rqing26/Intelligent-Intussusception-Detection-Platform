<template>
  <el-container class="app-layout">
    <el-header class="app-header">
      <div class="header-left">
        <!-- 侧栏折叠开关：窄屏会自动折叠，宽屏记住你上次的选择 -->
        <button
          class="nav-toggle"
          :title="isCollapse ? '展开导航栏' : '折叠导航栏'"
          :aria-label="isCollapse ? '展开导航栏' : '折叠导航栏'"
          :aria-expanded="!isCollapse"
          @click="toggleNav"
        >
          <el-icon :size="18">
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
        </button>
        <div class="header-brand">
          <img src="/newlogo.png" alt="logo" class="brand-icon" />
          <span class="brand-title">皖南医学院第一附属医院 肠套叠AI辅助诊断平台</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="theme-toggle" @click="handleToggleTheme" :title="currentTheme === 'modern' ? '切换至中世纪风格' : '切换至现代风格'">
          <span v-if="currentTheme === 'modern'">🏛</span>
          <span v-else>⚡</span>
          <span class="toggle-label">{{ currentTheme === 'modern' ? '手稿' : '现代' }}</span>
        </button>
        <div class="user-divider" />
        <span class="app-user">{{ auth.user?.full_name || auth.user?.username }}</span>
        <el-button text class="logout-btn" @click="handleLogout">
          退出登录
        </el-button>
      </div>
    </el-header>
    <el-container class="app-body">
      <el-aside :width="asideWidth" class="app-aside" :class="{ 'is-collapsed': isCollapse }">
        <el-menu
          :default-active="route.path"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          class="app-menu"
        >
          <el-menu-item index="/patients">
            <el-icon><User /></el-icon>
            <template #title>患者管理</template>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <template #title>检测记录</template>
          </el-menu-item>
          <el-menu-item v-if="isAdmin" index="/audit">
            <el-icon><Document /></el-icon>
            <template #title>审计日志</template>
          </el-menu-item>
        </el-menu>
        <!-- 折叠时侧栏只有 64px，医院署名放不下，整块隐藏 -->
        <div class="hospital-sidebar-brand" v-if="!isCollapse">
          <div class="sidebar-brand-line" />
          <div class="sidebar-brand-name">皖南医学院</div>
          <div class="sidebar-brand-sub">第一附属医院（弋矶山医院）</div>
        </div>
      </el-aside>
      <el-main class="app-main">
        <div class="hospital-watermark">
          <div class="watermark-text">皖南医学院第一附属医院</div>
          <div class="watermark-sub">弋矶山医院</div>
        </div>
        <div class="app-background-logo">
          <img src="/newlogo.png" alt="decorative logo" />
        </div>
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useSettingsStore } from '../stores/settings'
import { toggleTheme, getCurrentTheme } from '../utils/theme'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Document } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const settings = useSettingsStore()
const currentTheme = ref(getCurrentTheme())
const isAdmin = computed(() => auth.user?.role === 'admin')

// ---------------- 侧栏折叠 ----------------
const NAV_COLLAPSED_KEY = 'nav_collapsed'   // 记住用户的折叠选择
const NARROW_WIDTH = 1200                   // 小于这个宽度自动折叠（想改阈值改这里）
const COLLAPSED_WIDTH = '64px'
const EXPANDED_WIDTH = '220px'

const isCollapse = ref(false)
const isNarrow = ref(false)
const asideWidth = computed(() => (isCollapse.value ? COLLAPSED_WIDTH : EXPANDED_WIDTH))

function readPref() {
  try {
    return localStorage.getItem(NAV_COLLAPSED_KEY) === '1'
  } catch {
    return false
  }
}

function savePref(collapsed) {
  try {
    localStorage.setItem(NAV_COLLAPSED_KEY, collapsed ? '1' : '0')
  } catch {
    /* 隐私模式下 localStorage 可能不可用，忽略即可 */
  }
}

// 手动开关：始终以用户点击为准，并记住
function toggleNav() {
  isCollapse.value = !isCollapse.value
  savePref(isCollapse.value)
}

let mediaQuery = null

// 屏幕跨过断点时：进入窄屏自动折叠；回到宽屏恢复用户上次的选择
function handleNarrowChange(event) {
  isNarrow.value = event.matches
  isCollapse.value = event.matches ? true : readPref()
}

function bindMediaQuery() {
  if (typeof window === 'undefined' || !window.matchMedia) return
  mediaQuery = window.matchMedia(`(max-width: ${NARROW_WIDTH - 1}px)`)
  isNarrow.value = mediaQuery.matches
  isCollapse.value = mediaQuery.matches || readPref()
  // 兼容老 Safari：只有 addListener
  if (mediaQuery.addEventListener) mediaQuery.addEventListener('change', handleNarrowChange)
  else if (mediaQuery.addListener) mediaQuery.addListener(handleNarrowChange)
}

onMounted(() => {
  currentTheme.value = getCurrentTheme()
  bindMediaQuery()
})

onUnmounted(() => {
  if (!mediaQuery) return
  if (mediaQuery.removeEventListener) mediaQuery.removeEventListener('change', handleNarrowChange)
  else if (mediaQuery.removeListener) mediaQuery.removeListener(handleNarrowChange)
})

// ---------------- 主题 / 退出 ----------------
function handleToggleTheme() {
  const next = toggleTheme()
  currentTheme.value = next
  if (auth.user) {
    settings.updateTheme(next)
  }
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
  background: var(--bg-page);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 0 28px;
  box-shadow: var(--shadow-sm);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

/* 折叠开关按钮 */
.nav-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  padding: 0;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  font-family: var(--font-sans);
}

.nav-toggle:hover {
  border-color: var(--gold-dim);
  color: var(--text-primary);
}

.nav-toggle:focus-visible {
  outline: 2px solid var(--gold);
  outline-offset: 1px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.brand-icon {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.brand-title {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.theme-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all 0.2s;
  font-family: var(--font-sans);
}

.theme-toggle:hover {
  border-color: var(--gold-dim);
  color: var(--text-primary);
}

.toggle-label {
  font-size: 12px;
}

.user-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
}

.app-user {
  font-size: 13px;
  color: var(--text-secondary);
}

.logout-btn {
  color: var(--text-muted) !important;
  font-size: 13px;
}
.logout-btn:hover {
  color: var(--text-primary) !important;
}

.app-body {
  overflow: hidden;
}

.app-aside {
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  /* width 由 el-aside 的内联样式驱动，这里做过渡；折叠时裁掉跑出来的菜单文字 */
  transition: width 0.28s ease, background 0.35s ease;
  overflow: hidden;
  /* 让底部医院署名相对侧栏定位（否则会相对视口，折叠时位置会错） */
  position: relative;
}

.app-menu {
  background: transparent !important;
  border-right: none !important;
  padding: 16px 12px;
}

/* 折叠态：去掉左右内边距，把 64px 宽度让给图标居中 */
.app-menu.el-menu--collapse {
  padding: 16px 0;
}

/* 折叠态图标居中（Element Plus 会给菜单项加内联 padding-left，故用 !important 覆盖） */
:deep(.el-menu--collapse .el-menu-item) {
  padding: 0 20px !important;
}

:deep(.el-menu-item) {
  border-radius: var(--radius-sm);
  margin: 4px 0;
  height: 46px;
  line-height: 46px;
  color: var(--text-sidebar);
  transition: all 0.2s;
  font-family: var(--font-sans);
}

:deep(.el-menu-item .el-icon) {
  color: inherit;
}

:deep(.el-menu-item:hover) {
  background: var(--bg-sidebar-hover) !important;
  color: var(--text-inverse) !important;
}

:deep(.el-menu-item.is-active) {
  background: rgba(184, 148, 31, 0.12) !important;
  color: var(--text-sidebar-active) !important;
  font-weight: 700;
  box-shadow: inset 3px 0 0 var(--gold);
}

/* 折叠态下选中态左侧那条金色指示条贴边，观感更好 */
:deep(.el-menu--collapse .el-menu-item.is-active) {
  box-shadow: inset 2px 0 0 var(--gold);
}

.app-main {
  background: var(--bg-main);
  padding: 24px 28px;
  overflow-y: auto;
  position: relative;
}

.app-background-logo {
  position: fixed;
  bottom: 40px;
  right: 40px;
  width: 120px;
  height: 120px;
  pointer-events: none;
  z-index: 1;
  opacity: 0.08;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-background-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.hospital-watermark {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-30deg);
  pointer-events: none;
  z-index: 0;
  opacity: 0.04;
  text-align: center;
  user-select: none;
}
.watermark-text {
  font-size: 48px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 8px;
  white-space: nowrap;
  font-family: var(--font-display);
}
.watermark-sub {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 6px;
  margin-top: 8px;
  font-family: var(--font-display);
}

.hospital-sidebar-brand {
  position: absolute;
  bottom: 20px;
  left: 16px;
  right: 16px;
  text-align: center;
  padding-top: 12px;
}
.sidebar-brand-line {
  height: 1px;
  background: var(--gold-dim);
  opacity: 0.4;
  margin-bottom: 10px;
}
.sidebar-brand-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-inverse);
  opacity: 0.7;
  letter-spacing: 1px;
  font-family: var(--font-display);
}
.sidebar-brand-sub {
  font-size: 11px;
  color: var(--text-inverse);
  opacity: 0.5;
  margin-top: 2px;
  letter-spacing: 0.5px;
}

/* 中等宽度：标题压一压，避免和右侧操作区打架 */
@media (max-width: 1180px) {
  .app-header {
    padding: 0 16px;
  }
  .brand-title {
    font-size: 14px;
  }
  .app-main {
    padding: 20px 18px;
  }
}

/* 很窄：只留 logo 与必要操作 */
@media (max-width: 820px) {
  .brand-title {
    display: none;
  }
  .app-user,
  .toggle-label {
    display: none;
  }
  .hospital-watermark {
    display: none;
  }
  .app-background-logo {
    display: none;
  }
}
</style>
